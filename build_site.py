from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html import escape
from pathlib import Path
import shutil

from promessi_lessons.extract import collect_chapters, collect_lessons
from promessi_lessons.source import SourceBundle
from promessi_lessons.xml import NS


ROOT = Path(__file__).resolve().parent
DERIVATIVE_DIR = ROOT / "cc-by-nc-4.0-derivative-works"
SOURCE_FILENAME = "I promessi sposi Edizione semplificata.epub"
SOURCE_PATH = DERIVATIVE_DIR / "source" / "original" / SOURCE_FILENAME


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
    ("Lesson EPUBs", "lessons-epub", "One EPUB per subsection."),
    ("Lesson HTML", "lessons-html", "Minimal HTML with headings and local images where available."),
    ("Lesson TXT", "lessons-txt", "Plain text lessons for robust LMS import."),
    ("Chapter EPUBs", "chapters-epub", "One EPUB per chapter."),
    ("Original EPUB", "source", "The original, unmodified source EPUB used for reproducible builds."),
]


@dataclass(frozen=True)
class ChapterRow:
    number: int

    @property
    def basename(self) -> str:
        return f"Capitolo-{self.number:02d}"


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
        chapters = [ChapterRow(chapter.number) for chapter in collect_chapters(nodes)]
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
        "lessons-epub": DERIVATIVE_DIR / "generated" / "lessons-epub",
        "lessons-html": DERIVATIVE_DIR / "generated" / "lessons-html",
        "lessons-txt": DERIVATIVE_DIR / "generated" / "lessons-txt",
        "chapters-epub": DERIVATIVE_DIR / "generated" / "chapters-epub",
    }
    return {
        key: {path.name for path in directory.iterdir() if path.is_file()}
        if directory.exists()
        else set()
        for key, directory in roots.items()
    }


def artifact_link(label: str, href: str, available: bool) -> str:
    if available:
        return (
            f'<a class="pill pill-live" href="{escape(href, quote=True)}">'
            f"{escape(label)}</a>"
        )
    return f'<span class="pill pill-planned">{escape(label)}</span>'


def upstream_card(item: dict[str, str]) -> str:
    return (
        '<article class="resource-card">'
        f'<span class="resource-kind">{escape(item["kind"])}</span>'
        f'<h3><a href="{escape(item["href"], quote=True)}">{escape(item["title"])}</a></h3>'
        f"<p>{escape(item['description'])}</p>"
        "</article>"
    )


def overview_card(title: str, count: int, total: int, description: str) -> str:
    status = "ready" if count else "planned"
    return (
        '<article class="overview-card">'
        f'<span class="overview-label">{escape(title)}</span>'
        f"<strong>{count} / {total}</strong>"
        f"<p>{escape(description)}</p>"
        f'<span class="status-tag status-{status}">{status}</span>'
        "</article>"
    )


def surface_card(title: str, slug: str, description: str, existing: dict[str, set[str]], total: int) -> str:
    if slug == "source":
        count = 1 if SOURCE_PATH.exists() else 0
        expected = 1
    else:
        count = len(existing.get(slug, set()))
        expected = total
    status = f"{count} published" if count else "placeholder"
    return (
        '<article class="surface-card">'
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(description)}</p>"
        f'<div class="surface-meta"><span>{status}</span><span>{expected} expected</span></div>'
        "</article>"
    )


def lesson_row(lesson: LessonRow, existing: dict[str, set[str]]) -> str:
    html_name = f"{lesson.basename}.html"
    txt_name = f"{lesson.basename}.txt"
    epub_name = f"{lesson.basename}.epub"
    return (
        '<li class="lesson-row">'
        '<div class="lesson-copy">'
        f'<span class="lesson-kicker">Capitolo {lesson.chapter_number}</span>'
        f"<strong>{escape(lesson.label)}</strong>"
        "</div>"
        '<div class="pill-row">'
        + artifact_link("HTML", f"generated/lessons-html/{html_name}", html_name in existing["lessons-html"])
        + artifact_link("TXT", f"generated/lessons-txt/{txt_name}", txt_name in existing["lessons-txt"])
        + artifact_link("EPUB", f"generated/lessons-epub/{epub_name}", epub_name in existing["lessons-epub"])
        + "</div></li>"
    )


def chapter_block(
    chapter: ChapterRow,
    lessons: list[LessonRow],
    existing: dict[str, set[str]],
    open_by_default: bool,
) -> str:
    chapter_epub = f"{chapter.basename}.epub"
    summary = (
        f'<summary><div><span class="chapter-kicker">Chapter {chapter.number:02d}</span>'
        f"<h3>Capitolo {chapter.number}</h3></div>"
        f'<div class="summary-meta"><span>{len(lessons)} lessons</span>'
        + artifact_link(
            "Chapter EPUB",
            f"generated/chapters-epub/{chapter_epub}",
            chapter_epub in existing["chapters-epub"],
        )
        + "</div></summary>"
    )
    open_attr = " open" if open_by_default else ""
    items = "\n".join(lesson_row(lesson, existing) for lesson in lessons)
    return f'<details class="chapter-block"{open_attr}>{summary}<ol>{items}</ol></details>'


def build_html(chapters: list[ChapterRow], lessons: list[LessonRow], warnings: list[str]) -> str:
    existing = scan_existing_outputs()
    lesson_total = len(lessons)
    chapter_total = len(chapters)
    counts = Counter(lesson.chapter_number for lesson in lessons)

    overview = "\n".join(
        [
            overview_card("Lesson HTML", len(existing["lessons-html"]), lesson_total, "Minimal HTML exports."),
            overview_card("Lesson TXT", len(existing["lessons-txt"]), lesson_total, "Plain text lesson exports."),
            overview_card("Lesson EPUB", len(existing["lessons-epub"]), lesson_total, "One EPUB per subsection."),
            overview_card("Chapter EPUB", len(existing["chapters-epub"]), chapter_total, "One EPUB per chapter."),
        ]
    )
    upstream = "\n".join(upstream_card(item) for item in UPSTREAM_MATERIALS)
    surfaces = "\n".join(
        surface_card(title, slug, description, existing, chapter_total if slug == "chapters-epub" else lesson_total)
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
        warning_note = (
            '<div class="note"><strong>Parser note.</strong> '
            f"The source preserved {len(warnings)} numbering irregularity; this site keeps the original numbering."
            "</div>"
        )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Le Promesse Lezioni</title>
    <meta name="description" content="Lesson-sized exports derived from Leggiamo 102: I promessi sposi - edizione semplificata.">
    <link rel="stylesheet" href="site.css">
  </head>
  <body>
    <div class="page-shell">
      <header class="hero">
        <p class="eyebrow">GitHub Pages publication</p>
        <h1>Le Promesse Lezioni</h1>
        <p class="lede">
          Clean, lesson-sized exports derived from Andrea Petri's <em>Leggiamo 102:
          I promessi sposi - edizione semplificata</em>, prepared for import into
          systems such as LingQ.
        </p>
        <div class="hero-actions">
          <a class="button button-primary" href="source/original/{escape(SOURCE_FILENAME, quote=True)}">Original source EPUB</a>
          <a class="button button-secondary" href="https://leggiamoitaliano.weebly.com/italian-102.html">Upstream Italian 102</a>
          <a class="button button-secondary" href="ATTRIBUTION.md">Attribution</a>
        </div>
        <ul class="hero-stats">
          <li><strong>{chapter_total}</strong><span>chapters</span></li>
          <li><strong>{lesson_total}</strong><span>subsection lessons</span></li>
          <li><strong>{counts.get(10, 0)}</strong><span>chapter 10 lessons</span></li>
        </ul>
      </header>

      <main>
        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Alignment</p>
            <h2>Purpose of this derivative edition</h2>
          </div>
          <div class="three-up">
            <article class="mini-card">
              <h3>Open educational reuse</h3>
              <p>The upstream site frames the readings as OER and invites instructor adaptation.</p>
            </article>
            <article class="mini-card">
              <h3>Transformations, not replacement</h3>
              <p>This project preserves attribution while changing delivery format for study systems.</p>
            </article>
            <article class="mini-card">
              <h3>Clear separation</h3>
              <p>Code lives on the Apache-2.0 main branch; this branch publishes CC BY-NC 4.0 content.</p>
            </article>
          </div>
          <p class="fine-print">This page is an editorial/readability assessment, not legal advice.</p>
        </section>

        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Licensing</p>
            <h2>Code and content are intentionally separated</h2>
          </div>
          <div class="three-up">
            <article class="mini-card">
              <h3>Code: Apache-2.0</h3>
              <p>The exporter and build tooling live on the main branch under a software license.</p>
            </article>
            <article class="mini-card">
              <h3>Content: CC BY-NC 4.0</h3>
              <p>The source EPUB and generated artifacts remain attributed to Leggiamo! by Andrea Petri.</p>
            </article>
            <article class="mini-card">
              <h3>Original preserved</h3>
              <p>The linked source EPUB is the original, untransformed input used for reproducible builds.</p>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Upstream catalog</p>
            <h2>Material available from Leggiamo!</h2>
          </div>
          <div class="resource-grid">{upstream}</div>
        </section>

        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Artifacts</p>
            <h2>Current derived collection</h2>
          </div>
          <div class="overview-grid">{overview}</div>
          {warning_note}
          <p class="body-copy">
            The source EPUB yields {lesson_total} section-level lessons across {chapter_total} chapters.
            Chapters 1-9 and 11-16 each expose seven subsection lessons; chapter 10 exposes five.
          </p>
        </section>

        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Publishing surface</p>
            <h2>What this branch hosts</h2>
          </div>
          <div class="surface-grid">{surfaces}</div>
        </section>

        <section class="panel">
          <div class="section-heading">
            <p class="eyebrow">Lesson browser</p>
            <h2>Chapter-by-chapter lesson catalog</h2>
          </div>
          <div class="chapter-list">{chapters_html}</div>
        </section>
      </main>

      <footer class="site-footer">
        <p>
          Upstream-derived reading content is attributed to
          <a href="https://leggiamoitaliano.weebly.com/">Leggiamo!</a> by Andrea Petri under
          <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a>.
        </p>
        <p>The source code that generates this site and these artifacts lives separately on the Apache-2.0 main branch.</p>
      </footer>
    </div>
  </body>
</html>
"""


def write_static_files() -> None:
    DERIVATIVE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "site.css", DERIVATIVE_DIR / "site.css")
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
