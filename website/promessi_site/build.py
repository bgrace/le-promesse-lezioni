from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from importlib.resources import files
from pathlib import Path
import shutil
from string import Template

from promessi_lessons.audio import audio_relative_path
from promessi_lessons.extract import collect_chapters, collect_lessons
from promessi_lessons.paths import (
    BOOK_TITLE,
    book_path,
    chapter_path,
    lesson_path,
)
from promessi_lessons.source import SourceBundle
from promessi_lessons.xml import NS


def find_repo_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "ATTRIBUTION.md").exists() and (candidate / "justfile").exists():
            return candidate
    raise RuntimeError("Could not find repository root from the current working directory.")


ROOT = find_repo_root()
DERIVATIVE_DIR = ROOT / "cc-by-nc-4.0-derivative-works"
SOURCE_FILENAME = "I promessi sposi Edizione semplificata.epub"
SOURCE_PATH = DERIVATIVE_DIR / "source" / "original" / SOURCE_FILENAME
AUDIO_DIR = DERIVATIVE_DIR / "source" / "audio"
RESOURCE_ROOT = files("promessi_site") / "resources"
TEMPLATE_ROOT = RESOURCE_ROOT / "templates"


UPSTREAM_MATERIALS = [
    {
        "title": "This project",
        "kind": "Intent",
        "href": "https://leggiamoitaliano.weebly.com/this-project.html",
        "description": (
            "Andrea Petri explains the TPRS/OER goals: comprehensible Italian reading, "
            "community reuse, and instructor-led adaptations."
        ),
    },
    {
        "title": "Italian 101 readings",
        "kind": "Reading doc",
        "href": "https://docs.google.com/document/d/1SRreJvznRu8-_98IUB9YzbfG86ZUPQDPnx080zpGeKo/edit?usp=sharing",
        "description": "Master Google Doc for the Italian 101 sequence.",
    },
    {
        "title": "Italian 101 audio",
        "kind": "Audio folder",
        "href": "https://drive.google.com/drive/folders/1KFFDebjv9J_T9cIlbKP0mj-dYCuriWdU?usp=sharing",
        "description": "Public Google Drive folder with audio recordings for Italian 101.",
    },
    {
        "title": "Italian 102 readings",
        "kind": "Reading doc",
        "href": "https://docs.google.com/document/d/1kKUWgrMq1Q0Nv6dLQ91O1MpMdcYhuRdEpDlYN7MWmLg/edit?usp=sharing",
        "description": "Master Google Doc for the Italian 102 adaptation of I promessi sposi.",
    },
    {
        "title": "Italian 102 audio",
        "kind": "Audio folder",
        "href": "https://drive.google.com/open?id=1TiD-6KvTX-qJQxcDTVanjvv2DaD6BjGQ",
        "description": "Public Google Drive folder with audio recordings for Italian 102.",
    },
    {
        "title": "Blog / adaptation notes",
        "kind": "Community",
        "href": "https://leggiamoitaliano.weebly.com/blog/archives/11-2018",
        "description": "Upstream invites instructors to report modifications and alternate versions.",
    },
]


PUBLISHING_SURFACE = [
    ("EPUB collection", "epub", "Whole-book, chapter, and subsection EPUB exports."),
    ("HTML collection", "html", "Whole-book, chapter, and subsection HTML exports."),
    ("TXT collection", "txt", "Whole-book, chapter, and subsection plain text exports."),
    ("Audio collection", "audio", "Section-level MP3 files served directly from this site."),
    ("Original EPUB", "source", "The original, unmodified source EPUB used for reproducible builds."),
]


@dataclass(frozen=True)
class ChapterRow:
    number: int
    title: str

    @property
    def basename(self) -> str:
        return f"Capitolo-{self.number:02d}"

    @property
    def label(self) -> str:
        if self.title:
            return f"Capitolo {self.number} - {self.title}"
        return f"Capitolo {self.number}"


@dataclass(frozen=True)
class LessonRow:
    chapter_number: int
    section_number: int
    title: str

    @property
    def basename(self) -> str:
        return f"Capitolo-{self.chapter_number:02d}-{self.section_number:02d}"

    @property
    def label(self) -> str:
        return f"{self.chapter_number}.{self.section_number} {self.title}".strip()


def load_catalog() -> tuple[list[ChapterRow], list[LessonRow], list[str]]:
    source = SourceBundle.open(SOURCE_PATH)
    try:
        root = source.parse_root()
        body = root.find("x:body", NS)
        if body is None:
            raise RuntimeError("Source EPUB did not contain an XHTML body.")

        nodes = list(body)
        chapters = [ChapterRow(chapter.number, chapter.title) for chapter in collect_chapters(nodes)]
        lessons, warnings = collect_lessons(nodes)
        lesson_rows = [
            LessonRow(lesson.chapter_number, lesson.section_number, lesson.title)
            for lesson in lessons
        ]
        return chapters, lesson_rows, warnings
    finally:
        source.close()


def scan_existing_outputs() -> dict[str, set[str]]:
    roots = {
        "epub": DERIVATIVE_DIR / "generated" / "epub",
        "html": DERIVATIVE_DIR / "generated" / "html",
        "txt": DERIVATIVE_DIR / "generated" / "txt",
        "audio": AUDIO_DIR,
    }
    return {
        key: {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and (key != "audio" or path.suffix == ".mp3")
        }
        if directory.exists()
        else set()
        for key, directory in roots.items()
    }


@lru_cache
def load_template(name: str) -> Template:
    return Template((TEMPLATE_ROOT / name).read_text(encoding="utf-8"))


def render_template(name: str, **context: object) -> str:
    return load_template(name).substitute({key: str(value) for key, value in context.items()})


def artifact_link(label: str, href: str, available: bool) -> str:
    if available:
        return render_template(
            "artifact_link_live.html",
            href=escape(href, quote=True),
            label=escape(label),
        )
    return render_template("artifact_link_planned.html", label=escape(label))


def upstream_card(item: dict[str, str]) -> str:
    return render_template(
        "upstream_card.html",
        kind=escape(item["kind"]),
        href=escape(item["href"], quote=True),
        title=escape(item["title"]),
        description=escape(item["description"]),
    )


def overview_card(title: str, count: int, total: int, description: str) -> str:
    status = "ready" if count else "planned"
    return render_template(
        "overview_card.html",
        title=escape(title),
        count=count,
        total=total,
        description=escape(description),
        status=status,
    )


def surface_card(title: str, slug: str, description: str, existing: dict[str, set[str]], total: int) -> str:
    if slug == "source":
        count = 1 if SOURCE_PATH.exists() else 0
        expected = 1
    else:
        count = len(existing.get(slug, set()))
        expected = total
    status = f"{count} published" if count else "placeholder"
    return render_template(
        "surface_card.html",
        title=escape(title),
        description=escape(description),
        status=escape(status),
        expected=expected,
    )


def lesson_row(lesson: LessonRow, existing: dict[str, set[str]]) -> str:
    html_name = lesson_path("", lesson.chapter_number, lesson.section_number, lesson.title, "html").as_posix()
    txt_name = lesson_path("", lesson.chapter_number, lesson.section_number, lesson.title, "txt").as_posix()
    epub_name = lesson_path("", lesson.chapter_number, lesson.section_number, lesson.title, "epub").as_posix()
    audio_name = audio_relative_path(
        lesson.chapter_number,
        lesson.section_number,
        lesson.title,
    ).as_posix()
    artifact_links = "".join(
        [
            artifact_link("HTML", f"generated/html/{html_name}", html_name in existing["html"]),
            artifact_link("TXT", f"generated/txt/{txt_name}", txt_name in existing["txt"]),
            artifact_link("EPUB", f"generated/epub/{epub_name}", epub_name in existing["epub"]),
            artifact_link("AUDIO", f"source/audio/{audio_name}", audio_name in existing["audio"]),
        ]
    )
    return render_template(
        "lesson_row.html",
        chapter_number=lesson.chapter_number,
        label=escape(lesson.label),
        artifact_links=artifact_links,
    )


def chapter_block(
    chapter: ChapterRow,
    lessons: list[LessonRow],
    existing: dict[str, set[str]],
    open_by_default: bool,
) -> str:
    chapter_epub = chapter_path("", chapter.number, "epub").as_posix()
    chapter_html = chapter_path("", chapter.number, "html").as_posix()
    chapter_txt = chapter_path("", chapter.number, "txt").as_posix()
    artifact_links = "".join(
        [
            artifact_link("HTML", f"generated/html/{chapter_html}", chapter_html in existing["html"]),
            artifact_link("TXT", f"generated/txt/{chapter_txt}", chapter_txt in existing["txt"]),
            artifact_link("EPUB", f"generated/epub/{chapter_epub}", chapter_epub in existing["epub"]),
        ]
    )
    open_attr = " open" if open_by_default else ""
    lesson_rows = "\n".join(lesson_row(lesson, existing) for lesson in lessons)
    return render_template(
        "chapter_block.html",
        open_attr=open_attr,
        chapter_number_padded=f"{chapter.number:02d}",
        chapter_label=escape(chapter.label),
        lesson_count=len(lessons),
        artifact_links=artifact_links,
        lesson_rows=lesson_rows,
    )


def build_html(chapters: list[ChapterRow], lessons: list[LessonRow], warnings: list[str]) -> str:
    existing = scan_existing_outputs()
    lesson_total = len(lessons)
    chapter_total = len(chapters)
    collection_total = lesson_total + chapter_total + 1
    counts = Counter(lesson.chapter_number for lesson in lessons)
    normalized_epub = book_path("", "epub").as_posix()

    overview = "\n".join(
        [
            overview_card("HTML files", len(existing["html"]), collection_total, "Whole book, chapters, and lessons."),
            overview_card("TXT files", len(existing["txt"]), collection_total, "Whole book, chapters, and lessons."),
            overview_card("EPUB files", len(existing["epub"]), collection_total, "Whole book, chapters, and lessons."),
            overview_card("Lessons", lesson_total, lesson_total, "Subsection-level study units."),
        ]
    )
    upstream = "\n".join(upstream_card(item) for item in UPSTREAM_MATERIALS)
    surfaces = "\n".join(
        surface_card(
            title,
            slug,
            description,
            existing,
            1 if slug == "source" else lesson_total if slug == "audio" else collection_total,
        )
        for title, slug, description in PUBLISHING_SURFACE
    )
    chapters_html = "\n".join(
        chapter_block(
            chapter,
            [lesson for lesson in lessons if lesson.chapter_number == chapter.number],
            existing,
            open_by_default=index < 2,
        )
        for index, chapter in enumerate(chapters)
    )
    warning_note = ""
    if warnings:
        warning_note = render_template("warning_note.html", warning_count=len(warnings))

    return render_template(
        "page.html",
        book_title=escape(BOOK_TITLE),
        normalized_epub_link=artifact_link(
            "Normalized EPUB",
            f"generated/epub/{normalized_epub}",
            normalized_epub in existing["epub"],
        ),
        source_filename=escape(SOURCE_FILENAME, quote=True),
        chapter_total=chapter_total,
        lesson_total=lesson_total,
        chapter_10_lessons=counts.get(10, 0),
        upstream=upstream,
        overview=overview,
        warning_note=warning_note,
        surfaces=surfaces,
        chapters_html=chapters_html,
    )


def write_static_files() -> None:
    DERIVATIVE_DIR.mkdir(parents=True, exist_ok=True)
    (DERIVATIVE_DIR / "site.css").write_bytes((RESOURCE_ROOT / "site.css").read_bytes())
    shutil.copyfile(ROOT / "ATTRIBUTION.md", DERIVATIVE_DIR / "ATTRIBUTION.md")
    (DERIVATIVE_DIR / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    chapters, lessons, warnings = load_catalog()
    write_static_files()
    (DERIVATIVE_DIR / "index.html").write_text(
        build_html(chapters, lessons, warnings),
        encoding="utf-8",
    )
    print(f"Wrote {DERIVATIVE_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
