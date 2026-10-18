"""Dictionary coverage of lexically selective Chinese individual classifiers."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from scope import classify_classifier, load_classifier_scope


ROOT = Path(__file__).resolve().parent
LEADS = set("一二三四五六七八九十百千万亿兆两半几数整满全每这那某余０１２３４５６７８９0123456789")
BOUNDARIES = set("～｜。；，、：【】“”‘’（）()《》〈〉!！?？…·　 \t\n")
STATUSES = ("reference_a", "reference_b_example", "reference_b_text", "unmatched")
PAIR_FIELDS = (
    "target",
    "classifier",
    "frequency",
    "scope_category",
    "status",
    "example_id",
    "example",
)
REVIEW_FIELDS = PAIR_FIELDS + ("label", "route")


ADJUDICATION_ROUTES = {
    "valid_combination": "include",
    "approx_measure_word": "exclude",
    "event_classifier": "exclude",
    "container_measure_word": "exclude",
    "wrong_target_span": "drop",
    "wrong_classifier_marker": "drop",
    "non_nominal_target": "drop",
    "tokenization_or_lexicalization": "drop",
    "grammatically_wrong": "hold",
    "uncertain": "hold",
}


def load_adjudication(path: Path) -> dict[tuple[str, str], str]:
    """Return a pair-to-label mapping, rejecting any label without a route."""

    decisions = {}
    for row in read_csv(path):
        label = row["label"].strip()
        if label not in ADJUDICATION_ROUTES:
            raise ValueError(f"Unknown adjudication label: {label!r}")
        decisions[(row["target"], row["classifier"])] = label
    return decisions


def read_csv(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict], fields) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_record(row: dict[str, str]) -> tuple[str, str, str]:
    tagged = row["tagged"]
    classifier = "".join(row["classifier"].split())
    heads = re.findall(r"<h>(.*?)</h>", tagged)
    if len(heads) != 1 or tagged.count("<CL>") != 1 or not classifier:
        raise ValueError("Expected one target, one classifier marker and a classifier")
    target = "".join(heads[0].split())
    if not target:
        raise ValueError("Empty target")
    sentence = tagged.replace("<h>", "").replace("</h>", "").replace("<CL>", classifier)
    return target, classifier, sentence


def explicit_targets(text: str) -> set[str]:
    targets = set()
    for index, character in enumerate(text):
        if character != "～" or index == 0 or text[index - 1] not in LEADS:
            continue
        following = []
        for following_character in text[index + 1 :]:
            if following_character in BOUNDARIES:
                break
            if "一" <= following_character <= "鿿":
                following.append(following_character)
            if len(following) == 8:
                break
        if following:
            targets.add("".join(following))
    return targets


def load_references(
    directory: Path,
) -> tuple[set[tuple[str, str]], dict[str, tuple[str, set[str]]]]:
    first = {
        ("".join(row["noun"].split()), "".join(row["classifier"].split()))
        for row in read_csv(directory / "first.csv")
    }
    second = {}
    with (directory / "second.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            text = row["entry_text"].replace(" ", "").replace("　", "")
            second[row["classifier"]] = (text, explicit_targets(text))
    return first, second


def lookup(
    target: str,
    classifier: str,
    first: set[tuple[str, str]],
    second: dict[str, tuple[str, set[str]]],
) -> str:
    if (target, classifier) in first:
        return "reference_a"
    text, targets = second.get(classifier, ("", set()))
    if target in targets:
        return "reference_b_example"
    if target in text:
        return "reference_b_text"
    return "unmatched"


def _pair_rows(
    grouped_counts: Counter,
    examples: dict,
    first: set[tuple[str, str]],
    second: dict[str, tuple[str, set[str]]],
) -> list[dict]:
    """Build the output rows for one scope group.

    Every group is looked up, including the excluded and deferred ones. Scope is
    decided before lookup, so their status never enters the core coverage counts;
    it only tells a reviewer whether reference evidence happens to exist for a
    pair the configuration kept out of the core experiment.
    """

    rows = []
    for (category, target, classifier), frequency in sorted(grouped_counts.items()):
        record_id, sentence = examples[(category, target, classifier)]
        rows.append(
            {
                "target": target,
                "classifier": classifier,
                "frequency": frequency,
                "scope_category": category,
                "status": lookup(target, classifier, first, second),
                "example_id": record_id,
                "example": sentence,
            }
        )
    return rows


def _coverage(pairs: list[dict]) -> list[dict]:
    """Return type and token counts per evidence status for one set of pairs."""

    summary = []
    for status in STATUSES:
        subset = [pair for pair in pairs if pair["status"] == status]
        summary.append(
            {
                "status": status,
                "types": len(subset),
                "tokens": sum(pair["frequency"] for pair in subset),
            }
        )
    return summary


def analyze(
    rows: list[dict[str, str]],
    first: set[tuple[str, str]],
    second: dict[str, tuple[str, set[str]]],
    scope: dict[str, dict[str, str]],
    output: Path,
    decisions: dict[tuple[str, str], dict[str, str]] | None = None,
) -> dict:
    grouped = {
        "include": Counter(),
        "exclude": Counter(),
        "review": Counter(),
    }
    examples = {"include": {}, "exclude": {}, "review": {}}
    invalid = []
    seen = set()
    sources = Counter()

    for row in rows:
        source = row["id"].split("_", 1)[0]
        if source not in {"LCMC", "UCLA"}:
            continue
        try:
            if row["id"] in seen:
                raise ValueError("Duplicate id")
            target, classifier, sentence = parse_record(row)
        except (KeyError, ValueError) as error:
            invalid.append({"id": row.get("id", ""), "reason": str(error)})
            continue

        seen.add(row["id"])
        sources[source] += 1
        scope_entry = classify_classifier(classifier, scope)
        decision = scope_entry["decision"]
        key = (scope_entry["category"], target, classifier)
        grouped[decision][key] += 1
        examples[decision].setdefault(key, (row["id"], sentence))

    core_pairs = _pair_rows(grouped["include"], examples["include"], first, second)
    excluded_pairs = _pair_rows(grouped["exclude"], examples["exclude"], first, second)
    review_pairs = _pair_rows(grouped["review"], examples["review"], first, second)

    coverage_summary = _coverage(core_pairs)


    decisions = decisions or {}
    routed = {"include": [], "exclude": [], "drop": [], "hold": []}
    for pair in review_pairs:
        label = decisions.get((pair["target"], pair["classifier"]), "unadjudicated")
        pair["label"] = label
        pair["route"] = ADJUDICATION_ROUTES.get(label, "hold")
        routed[pair["route"]].append(pair)

    adjudicated_core = core_pairs + [
        {**pair, "scope_category": "adjudicated_individual"} for pair in routed["include"]
    ]
    adjudicated_coverage = _coverage(adjudicated_core)

    scope_summary = []
    for decision, pair_rows in (
        ("include", core_pairs),
        ("exclude", excluded_pairs),
        ("review", review_pairs),
    ):
        categories = sorted({pair["scope_category"] for pair in pair_rows})
        for category in categories:
            subset = [pair for pair in pair_rows if pair["scope_category"] == category]
            scope_summary.append(
                {
                    "scope_decision": decision,
                    "scope_category": category,
                    "classifiers": " ".join(sorted({pair["classifier"] for pair in subset})),
                    "types": len(subset),
                    "tokens": sum(pair["frequency"] for pair in subset),
                }
            )

    valid_tokens = sum(sources.values())
    included_tokens = sum(pair["frequency"] for pair in core_pairs)
    excluded_tokens = sum(pair["frequency"] for pair in excluded_pairs)
    review_tokens = sum(pair["frequency"] for pair in review_pairs)
    if included_tokens + excluded_tokens + review_tokens != valid_tokens:
        raise AssertionError("Scope token totals do not reconcile with valid records")

    def _counts(pairs: list[dict]) -> dict:
        return {"types": len(pairs), "tokens": sum(pair["frequency"] for pair in pairs)}

    if sum(_counts(pairs)["tokens"] for pairs in routed.values()) != review_tokens:
        raise AssertionError("Adjudication token totals do not reconcile with the review scope")

    run_summary = {
        "valid_records": valid_tokens,
        "invalid_records": len(invalid),
        "sources": dict(sorted(sources.items())),
        "scope": {
            "include": {"types": len(core_pairs), "tokens": included_tokens},
            "exclude": {"types": len(excluded_pairs), "tokens": excluded_tokens},
            "review": {"types": len(review_pairs), "tokens": review_tokens},
        },
        "coverage": coverage_summary,
        "adjudication": {
            "routes": {route: _counts(pairs) for route, pairs in routed.items()},
            "core_after_adjudication": _counts(adjudicated_core),
            "coverage_after_adjudication": adjudicated_coverage,
        },
        "scope_config": "classifier_scope.json",
    }

    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "pairs.csv", core_pairs, PAIR_FIELDS)
    write_csv(output / "summary.csv", coverage_summary, ("status", "types", "tokens"))
    write_csv(output / "scope_excluded.csv", excluded_pairs, PAIR_FIELDS)
    write_csv(output / "scope_review.csv", review_pairs, REVIEW_FIELDS)
    write_csv(
        output / "scope_summary.csv",
        scope_summary,
        ("scope_decision", "scope_category", "classifiers", "types", "tokens"),
    )
    write_csv(
        output / "adjudicated_summary.csv",
        adjudicated_coverage,
        ("status", "types", "tokens"),
    )
    write_csv(output / "invalid.csv", invalid, ("id", "reason"))
    with (output / "run_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(run_summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    print(
        f"Valid records: {valid_tokens}; core pairs: {len(core_pairs)}; "
        f"excluded pairs: {len(excluded_pairs)}; review pairs: {len(review_pairs)}; "
        f"invalid: {len(invalid)}"
    )
    print(f"Sources: {dict(sources)}")
    for row in coverage_summary:
        print(row)
    if decisions:
        routes = ", ".join(f"{route}={len(pairs)}" for route, pairs in routed.items())
        print(f"After adjudication -- core pairs: {len(adjudicated_core)}; routes: {routes}")
        for row in adjudicated_coverage:
            print(row)
    return run_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "private_data")
    parser.add_argument("--scope", type=Path, default=ROOT / "classifier_scope.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use invented, redistributable examples",
    )
    args = parser.parse_args()
    scope = load_classifier_scope(args.scope)
    if args.demo:
        rows = [
            {"id": "LCMC_1", "tagged": "一 <CL> <h>书</h>", "classifier": "本"},
            {"id": "LCMC_2", "tagged": "一 <CL> <h>船</h>", "classifier": "艘"},
            {"id": "LCMC_3", "tagged": "一 <CL> <h>学生</h>", "classifier": "个"},
            {"id": "LCMC_4", "tagged": "一 <CL> <h>水</h>", "classifier": "口"},
        ]
        first = {("\u4e66", "\u672c")}
        second = {"艘": ("一～船。", {"船"})}
        decisions = {}
    else:
        rows = read_csv(args.data / "corpus.csv")
        first, second = load_references(args.data)
        decisions = load_adjudication(ROOT / "adjudication.csv")
    analyze(rows, first, second, scope, args.output, decisions)


if __name__ == "__main__":
    main()
