"""Load and validate the classifier scope used by the core experiment."""

from __future__ import annotations

import json
from pathlib import Path


VALID_DECISIONS = frozenset({"include", "exclude", "review"})


def load_classifier_scope(path: Path) -> dict[str, dict[str, str]]:
    """Return a classifier-to-scope mapping from the public JSON config."""

    with Path(path).open(encoding="utf-8") as stream:
        raw = json.load(stream)

    unknown_decisions = set(raw) - VALID_DECISIONS
    if unknown_decisions:
        raise ValueError(
            "Unknown scope decisions: " + ", ".join(sorted(unknown_decisions))
        )

    mapping: dict[str, dict[str, str]] = {}
    for decision in ("include", "exclude", "review"):
        categories = raw.get(decision, {})
        if not isinstance(categories, dict):
            raise ValueError(f"Scope section {decision!r} must be an object")
        for category, specification in categories.items():
            description = specification.get("description", "").strip()
            classifiers = specification.get("classifiers", [])
            if not description:
                raise ValueError(f"Missing description for scope category {category}")
            if not isinstance(classifiers, list):
                raise ValueError(f"Classifiers for {category} must be a list")
            for raw_classifier in classifiers:
                classifier = "".join(str(raw_classifier).split())
                if not classifier:
                    raise ValueError(f"Empty classifier in scope category {category}")
                if classifier in mapping:
                    previous = mapping[classifier]
                    raise ValueError(
                        f"Classifier {classifier!r} occurs in both "
                        f"{previous['category']!r} and {category!r}"
                    )
                mapping[classifier] = {
                    "decision": decision,
                    "category": category,
                    "description": description,
                }
    return mapping


def classify_classifier(
    classifier: str,
    scope: dict[str, dict[str, str]],
) -> dict[str, str]:
    """Classify one form; unseen forms default to review, never inclusion."""

    return scope.get(
        classifier,
        {
            "decision": "review",
            "category": "unlisted",
            "description": "Classifier absent from classifier_scope.json.",
        },
    )
