from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path


SECTION_HEADING = re.compile(r"^[A-Z]$")
PARENTHETICAL = re.compile(r"[（(].*?[）)]")


def parse_first_reference(path: Path) -> dict[str, frozenset[str]]:
    """Parse the noun-to-classifier appendix from the first reference book."""

    entries: dict[str, set[str]] = defaultdict(set)
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text or SECTION_HEADING.fullmatch(text):
                continue

            parts = re.split(r"\s+", text, maxsplit=1)
            if len(parts) == 1:
                joined = re.match(r"^(.*?）)(.+)$", text)
                if joined is None:
                    raise ValueError(
                        f"Cannot parse first-reference line {line_number}: {text}"
                    )
                noun_field, classifier_field = joined.groups()
            else:
                noun_field, classifier_field = parts

            noun = PARENTHETICAL.sub("", noun_field).strip()
            for item in classifier_field.split("，"):
                classifier = PARENTHETICAL.sub("", item).strip()
                if classifier:
                    entries[noun].add(classifier)

    return {noun: frozenset(values) for noun, values in entries.items()}

