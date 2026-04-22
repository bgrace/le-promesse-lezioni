Project: I promessi sposi — Edizione semplificata

Goal
- Prepare the ebook content for study in LingQ by splitting the checked-in source EPUB into small, uploadable lessons (a few minutes each), ideally at subsection granularity.

Key Files and Layout
- Checked-in source EPUB: `source/I promessi sposi Edizione semplificata.epub`
- Script: `split_chapters.py` (Python 3, no external deps)
- Project metadata: `pyproject.toml`
- Lockfile: `uv.lock`
- Task runner: `justfile`
- Generated outputs:
  - Per-subsection EPUB: `generated/lessons-epub/Capitolo-XX-YY.epub`
  - Per-subsection HTML: `generated/lessons-html/Capitolo-XX-YY.html`
  - Per-subsection TXT: `generated/lessons-txt/Capitolo-XX-YY.txt`
  - Per-chapter EPUB: `generated/chapters-epub/Capitolo-XX.epub`

How Chapters and Sections Are Marked in the Source
- The source EPUB contains an XHTML document with chapter headers like `<h2>…Capitolo N…</h2>`
- Subsection headers are `<h3>…N.M Title…</h3>` (for example `1.1 Don Abbondio`)
- There are 16 chapters; subsections per chapter vary. Numbering may skip (e.g., some chapters don’t have a “.01” entry); this is expected from the source.

Splitter Script Overview (`split_chapters.py`)
- Language: Python 3 (stdlib `xml.etree.ElementTree`)
- Inputs:
  - Source can be either the checked-in EPUB or a standalone XHTML file
- Modes:
  - `--by=sections` (default): each `<h3>` subsection becomes one lesson
  - `--by=chapters`: each `<h2>` chapter becomes one lesson
- Formats:
  - `--format=epub` (default): valid EPUB 3 package per lesson with CSS, nav, metadata, and embedded local images
  - `--format=html`: minimal `<head>` (UTF‑8) + content; keeps headings; keeps inline links/images
  - `--format=txt`: plain text; headings included; double newlines between blocks; images omitted
- Resource handling:
  - HTML: referenced images are copied into `images/` under the output directory
  - EPUB: referenced images are embedded into each lesson archive
  - Google redirect links are unwrapped and broken local fragment links are removed from packaged output

Usage
- Subsection EPUB lessons (recommended default):
  - `just lessons-epub`
  - Raw command: `uv run python3 split_chapters.py "source/I promessi sposi Edizione semplificata.epub" generated/lessons-epub`
- Subsection HTML lessons:
  - `just lessons-html`
- Subsection TXT lessons:
  - `just lessons-txt`
- Per-chapter EPUB lessons:
  - `just chapters-epub`
- EPUB validation:
  - `just check-epub`

LingQ Import Notes (practical)
- LingQ accepts both plain text and simple HTML via the web UI. Minimal HTML keeps headings and images; TXT is most robust if you don’t need images/formatting.
- Short lessons import and review better; subsection splitting aligns well with “a few minutes per lesson”.
- External links (e.g., Google Drive “FILE AUDIO”) are preserved in HTML; they will appear as clickable links inside lessons.

What’s Already Done
- Added EPUB export so each lesson can be emitted as a standalone ebook with embedded images; this is now the default output mode.
- Set the repo up as a `uv` project with an installed `split-chapters` console entry point.
- Added a `justfile` for common export and validation tasks.
- Moved the project to use the checked-in source EPUB directly, with generated output isolated under `generated/`.

Limitations / Considerations
- Minimal HTML output intentionally omits the original document’s massive inline CSS to keep imports clean.
- Section boundaries are strictly based on `<h3>` markers; content runs until the next `<h3>` or the next chapter header.
- Numbering and titles come from the document; the script doesn’t renumber or normalize missing/extra segments.

Suggested Enhancements (see TODO.org for tasks)
- Optional length‑based splitting to target precise reading time per lesson
- Gloss removal (e.g., parenthetical English hints like “(=priest)”) for a cleaner reading pass
- Packaging jobs (ZIP) for batch import convenience
- Sanitize step (strip tracking params from external links)
