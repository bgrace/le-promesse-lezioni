from __future__ import annotations

from pathlib import Path
import re
import unicodedata


BOOK_TITLE = "I promessi sposi - Edizione semplificata"


def slug_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-")
    return slug or "Senza-titolo"


def book_stem() -> str:
    return slug_text(BOOK_TITLE)


def chapter_stem(chapter_number: int) -> str:
    return f"Capitolo-{chapter_number:02d}"


def lesson_stem(chapter_number: int, section_number: int, title: str) -> str:
    return f"{chapter_number:02d}-{section_number:02d}-{slug_text(title)}"


def book_path(out_dir: str | Path, out_format: str) -> Path:
    return Path(out_dir) / f"{book_stem()}.{out_format}"


def chapter_path(out_dir: str | Path, chapter_number: int, out_format: str) -> Path:
    return Path(out_dir) / f"{chapter_stem(chapter_number)}.{out_format}"


def lesson_path(
    out_dir: str | Path,
    chapter_number: int,
    section_number: int,
    title: str,
    out_format: str,
) -> Path:
    return (
        Path(out_dir)
        / chapter_stem(chapter_number)
        / f"{lesson_stem(chapter_number, section_number, title)}.{out_format}"
    )
