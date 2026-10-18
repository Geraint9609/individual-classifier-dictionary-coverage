import csv
import json
import tempfile
import unittest
from pathlib import Path

from main import analyze, explicit_targets, load_adjudication, lookup, parse_record
from scope import classify_classifier, load_classifier_scope


ROOT = Path(__file__).resolve().parent


class ParsingTests(unittest.TestCase):
    def test_parse_record(self):
        target, classifier, sentence = parse_record(
            {"tagged": "一 <CL> <h>战斗 机</h>", "classifier": " 架 "}
        )
        self.assertEqual(target, "战斗机")
        self.assertEqual(classifier, "架")
        self.assertIn("架", sentence)

    def test_parse_record_rejects_multiple_targets(self):
        with self.assertRaises(ValueError):
            parse_record(
                {
                    "tagged": "一 <CL> <h>书</h> 和 <h>报纸</h>",
                    "classifier": "本",
                }
            )

    def test_explicit_targets(self):
        self.assertEqual(explicit_targets("一～船。两～飞机；"), {"船", "飞机"})


class LookupTests(unittest.TestCase):
    def test_lookup_priority(self):
        first = {("\u4e66", "\u672c")}
        second = {"本": ("一～书。", {"书"})}
        self.assertEqual(lookup("书", "本", first, second), "reference_a")
        self.assertEqual(
            lookup("船", "艘", set(), {"艘": ("一～船。", {"船"})}),
            "reference_b_example",
        )
        self.assertEqual(
            lookup("飞机", "架", set(), {"架": ("飞机可用架计数", set())}),
            "reference_b_text",
        )
        self.assertEqual(lookup("星球", "颗", set(), {}), "unmatched")


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.scope = load_classifier_scope(ROOT / "classifier_scope.json")

    def test_scope_contains_requested_exclusions(self):
        for classifier in ("个", "位", "名"):
            self.assertEqual(
                classify_classifier(classifier, self.scope)["decision"],
                "exclude",
            )
        for classifier in ("张", "本", "辆"):
            self.assertEqual(
                classify_classifier(classifier, self.scope)["decision"],
                "include",
            )

    def test_unlisted_classifier_defaults_to_review(self):
        result = classify_classifier("测试量词", self.scope)
        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["category"], "unlisted")

    def test_duplicate_scope_entry_is_rejected(self):
        content = {
            "include": {
                "a": {"description": "a", "classifiers": ["本"]},
            },
            "exclude": {
                "b": {"description": "b", "classifiers": ["本"]},
            },
            "review": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scope.json"
            path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_classifier_scope(path)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.scope = load_classifier_scope(ROOT / "classifier_scope.json")

    def test_analyze_separates_core_excluded_and_review(self):
        rows = [
            {"id": "LCMC_1", "tagged": "一 <CL> <h>书</h>", "classifier": "本"},
            {"id": "LCMC_2", "tagged": "一 <CL> <h>学生</h>", "classifier": "个"},
            {"id": "UCLA_1", "tagged": "喝 一 <CL> <h>水</h>", "classifier": "口"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = analyze(rows, {("\u4e66", "\u672c")}, {}, self.scope, output)
            self.assertEqual(result["scope"]["include"], {"types": 1, "tokens": 1})
            self.assertEqual(result["scope"]["exclude"], {"types": 1, "tokens": 1})
            self.assertEqual(result["scope"]["review"], {"types": 1, "tokens": 1})
            with (output / "pairs.csv").open(encoding="utf-8", newline="") as stream:
                pairs = list(csv.DictReader(stream))
            self.assertEqual([(row["target"], row["classifier"]) for row in pairs], [("书", "本")])

    def test_adjudication_routes_a_review_pair_into_the_core(self):
        rows = [
            {"id": "LCMC_1", "tagged": "一 <CL> <h>书</h>", "classifier": "本"},
            {"id": "UCLA_1", "tagged": "喝 一 <CL> <h>水</h>", "classifier": "口"},
        ]
        decisions = {("水", "口"): "valid_combination"}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = analyze(
                rows, {("\u4e66", "\u672c")}, {}, self.scope, output, decisions
            )
            adjudication = result["adjudication"]
            self.assertEqual(adjudication["routes"]["include"], {"types": 1, "tokens": 1})
            self.assertEqual(adjudication["core_after_adjudication"], {"types": 2, "tokens": 2})
            # The automatic result must be unchanged by the manual layer.
            self.assertEqual(result["scope"]["include"], {"types": 1, "tokens": 1})
            self.assertEqual(result["scope"]["review"], {"types": 1, "tokens": 1})

    def test_unknown_adjudication_label_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adjudication.csv"
            path.write_text("target,classifier,label\n书,本,not_a_label\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_adjudication(path)

    def test_duplicate_id_is_reported_invalid(self):
        rows = [
            {"id": "LCMC_1", "tagged": "一 <CL> <h>书</h>", "classifier": "本"},
            {"id": "LCMC_1", "tagged": "一 <CL> <h>船</h>", "classifier": "艘"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            result = analyze(rows, set(), {}, self.scope, Path(directory))
            self.assertEqual(result["valid_records"], 1)
            self.assertEqual(result["invalid_records"], 1)


if __name__ == "__main__":
    unittest.main()
