#!/usr/bin/env python3
"""Build main.py-compatible local extracts from authorized source materials."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from dictionary_pdf import extract_classifier_entries
from lexicon import parse_first_reference


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first-reference", required=True, type=Path)
    parser.add_argument("--second-reference-pdf", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    first = parse_first_reference(args.first_reference)
    first_rows = [
        {"noun": noun, "classifier": classifier}
        for noun, classifiers in sorted(first.items())
        for classifier in sorted(classifiers)
    ]
    with (args.output_dir / "first.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=["noun", "classifier"])
        writer.writeheader()
        writer.writerows(first_rows)

    second = extract_classifier_entries(args.second_reference_pdf)
    with (args.output_dir / "second.jsonl").open("w", encoding="utf-8") as stream:
        for classifier, entry in sorted(second.items()):
            stream.write(
                json.dumps(
                    {
                        "classifier": classifier,
                        "entry_text": entry.text,
                        "book_pages": list(entry.book_pages),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(
        f"Wrote {len(first_rows)} first-reference pairs and "
        f"{len(second)} second-reference entries to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
