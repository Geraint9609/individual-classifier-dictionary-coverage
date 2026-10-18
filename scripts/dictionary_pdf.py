from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ENTRY_HEADING = re.compile(r"^(.+?)\s*［")


@dataclass(frozen=True, slots=True)
class DictionaryEntry:
    classifier: str
    text: str
    book_pages: tuple[int, ...]


def _heading_lemma(line: str) -> str | None:
    match = ENTRY_HEADING.match(line.strip())
    if match is None:
        return None
    lemma = match.group(1).strip()
    if not lemma or len(lemma) > 12:
        return None
    if any(character in lemma for character in "。【】，：｜"):
        return None
    return lemma


def _normalize_entry_text(text: str) -> str:
    return text.replace(" ", "").replace("　", "")


def extract_classifier_entries(
    pdf_path: Path,
    *,
    body_start_pdf_page: int = 24,
    body_end_pdf_page: int = 303,
) -> dict[str, DictionaryEntry]:
    """Extract classifier entry blocks from the 2013 dictionary PDF.

    PDF page 24 is printed dictionary page 1. Page values in returned entries
    use the printed book pagination so a human reviewer can find the evidence.
    """

    try:
        from pypdf import PdfReader
    except ImportError as error:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "PDF support requires pypdf. Install with: pip install -r requirements-extraction.txt"
        ) from error

    reader = PdfReader(Path(pdf_path))
    if not 1 <= body_start_pdf_page <= body_end_pdf_page <= len(reader.pages):
        raise ValueError("Configured dictionary body pages are outside the PDF.")

    raw_entries: dict[str, list[tuple[str, set[int]]]] = defaultdict(list)
    current_lemma: str | None = None
    current_lines: list[str] = []
    current_pages: set[int] = set()

    def finish_entry() -> None:
        nonlocal current_lemma, current_lines, current_pages
        if current_lemma is None:
            return
        raw_entries[current_lemma].append(
            ("".join(current_lines), set(current_pages))
        )

    for pdf_page in range(body_start_pdf_page, body_end_pdf_page + 1):
        page_text = reader.pages[pdf_page - 1].extract_text() or ""
        printed_page = pdf_page - body_start_pdf_page + 1
        for line in page_text.splitlines():
            stripped = line.strip()
            lemma = _heading_lemma(stripped)
            if lemma is not None:
                finish_entry()
                current_lemma = lemma
                current_lines = [stripped]
                current_pages = {printed_page}
                continue
            if current_lemma is not None:
                current_lines.append(stripped)
                current_pages.add(printed_page)
    finish_entry()

    entries: dict[str, DictionaryEntry] = {}
    for lemma, blocks in raw_entries.items():
        text = _normalize_entry_text("".join(block[0] for block in blocks))
        pages = tuple(sorted({page for _, block_pages in blocks for page in block_pages}))
        entries[lemma] = DictionaryEntry(lemma, text, pages)
    return entries
