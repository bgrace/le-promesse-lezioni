Project: I promessi sposi — Edizione semplificata

Goal
- Prepare the Leggiamo! Italian 102 material for study in LingQ and similar language-learning systems by splitting it into small, uploadable lessons, ideally at subsection granularity.
- Keep the Apache-2.0 source-code branch cleanly separated from CC BY-NC 4.0 source/derived content.

Branch and License Model
- `main` is the code/tooling/docs branch and is licensed under Apache-2.0.
- `main` must not track the upstream source EPUB or generated derived lesson artifacts.
- `gh-pages` is an orphan publication branch for CC BY-NC 4.0 material. It contains the static site, original source EPUB, imported audio, generated lesson artifacts, and attribution notice.
- A user who checks out only `main` should not receive a copy of the upstream-derived source or generated content.
- Upstream-derived content attribution is documented in `ATTRIBUTION.md`.

Key Files and Layout on `main`
- Lesson material uv project: `lesson-material/`
- Lesson script entry point: `lesson-material/split_chapters.py`
- Lesson source package: `lesson-material/promessi_lessons/`
- Source-copy helper: `lesson-material/promessi_lessons/prepare_source.py`
- EPUB validation helper: `lesson-material/promessi_lessons/check_epubs.py`
- Website uv project: `website/`
- GitHub Pages generator: `website/promessi_site/build.py`
- Site stylesheet source: `website/promessi_site/resources/site.css`
- Site templates: `website/promessi_site/resources/templates/`
- Project metadata and lockfiles: `lesson-material/pyproject.toml`, `lesson-material/uv.lock`, `website/pyproject.toml`, `website/uv.lock`
- Task runner: `justfile`
- Code license: `LICENSE`
- Content attribution: `ATTRIBUTION.md`

Ignored CC BY-NC Local Build Directory
- Local source and generated artifacts go under:
  - `cc-by-nc-4.0-derivative-works/`
- This directory is ignored by git on `main`.
- Copied source EPUB:
  - `cc-by-nc-4.0-derivative-works/source/original/I promessi sposi Edizione semplificata.epub`
- Imported source audio:
  - `cc-by-nc-4.0-derivative-works/source/audio/`
- Generated outputs:
  - EPUB collection: `cc-by-nc-4.0-derivative-works/generated/epub/`
  - HTML collection: `cc-by-nc-4.0-derivative-works/generated/html/`
  - TXT collection: `cc-by-nc-4.0-derivative-works/generated/txt/`
  - Whole-book files: `I-promessi-sposi-Edizione-semplificata.{epub,html,txt}` at the top of each format directory.
  - Per-chapter files: `Capitolo-XX.{epub,html,txt}` at the top of each format directory.
  - Per-section files: `Capitolo-XX/XX-YY-Section-title.{epub,html,txt}` under each format directory.
  - Static site: `cc-by-nc-4.0-derivative-works/index.html`, `site.css`, `.nojekyll`, `ATTRIBUTION.md`

Canonical Source Handling
- The canonical original EPUB is stored on `gh-pages` at:
  - `source/original/I promessi sposi Edizione semplificata.epub`
- `promessi-prepare-source` copies that EPUB from `gh-pages` or `origin/gh-pages` into the ignored local build directory.
- For migration compatibility, the source helper also recognizes the old `gh-pages:source/I promessi sposi Edizione semplificata.epub` path.

How Chapters and Sections Are Marked in the Source
- The source EPUB contains an XHTML document with chapter headers like `<h2>...Capitolo N...</h2>`.
- Subsection headers are `<h3>...N.M Title...</h3>` (for example `1.1 Don Abbondio`).
- There are 16 chapters and 112 subsection lessons.
- Some source headings contain spacing irregularities such as `10 .5`; parse them as source numbering, not as renumbering instructions.

Splitter Script Overview
- Language: Python 3.
- The exporter is packaged as the `lesson-material/` uv project; the website is packaged separately under `website/`.
- Input can be an EPUB or standalone XHTML file.
- Modes:
  - `--by=all` (default): emits the normalized whole book, chapter files, and section files in one format directory.
  - `--by=book`: emits one normalized whole-book file.
  - `--by=sections`: each `<h3>` subsection becomes one lesson grouped under its chapter directory.
  - `--by=chapters`: each `<h2>` chapter becomes one lesson.
- Formats:
  - `--format=epub` (default): valid EPUB 3 package per lesson with CSS, nav, metadata, and embedded local images.
  - `--format=html`: minimal `<head>` plus content; keeps headings, inline links, and images.
  - `--format=txt`: plain text; headings included; images omitted.
- Cleanup transforms:
  - Strip page-break artifacts.
  - Unwrap Google redirect links.
  - Remove broken local fragment links from packaged output.
  - Strip `FILE AUDIO` links from generated products until audio hosting is resolved.
  - Strip inline English glosses by default, such as `rammarico (= regret)`.
  - Use `--keep-english-annotations` to preserve those glosses.

Usage
- Set up environment:
  - `just setup-worktree`
- Full local build:
  - `just build`
- Copy source only:
  - `just prepare-source`
- Import source audio:
  - `just import-audio`
- EPUB collection:
  - `just lessons-epub`
- HTML collection:
  - `just lessons-html`
- TXT collection:
  - `just lessons-txt`
- Chapter-only EPUB rebuild:
  - `just chapters-epub`
- Build static site only:
  - `just site`
- Preview static site locally:
  - `just preview`
- EPUB validation:
  - `just check-epub`
- Clean generated files while keeping copied source:
  - `just clean`
- Remove the entire ignored derivative directory:
  - `just clean-all`

Publishing Branch Shape
- `gh-pages` should remain an orphan branch, not descended from `main`.
- `gh-pages` should contain only:
  - `.nojekyll`
  - `ATTRIBUTION.md`
  - `index.html`
  - `site.css`
  - `source/original/I promessi sposi Edizione semplificata.epub`
  - `source/audio/...`
  - `generated/...`
- `gh-pages` should not contain Python source, `pyproject.toml`, `uv.lock`, `justfile`, Apache `LICENSE`, or repo tooling.

LingQ Import Notes
- LingQ accepts plain text and simple HTML via the web UI.
- TXT is most robust if images and formatting are not needed.
- Minimal HTML keeps headings and images.
- Short subsection lessons import and review better than large chapter-size files.
- External links are preserved when useful, but source `FILE AUDIO` heading clutter is stripped from generated products.
- Imported audio is cross-linked into section-level HTML lessons and the static site catalog when present locally.

Verification Expectations
- `just build` should produce 129 files per generated format: 1 whole-book file, 16 chapter files, and 112 section files.
- `just check-epub` should validate 129 EPUBs.
- `git status --ignored` on `main` should show `cc-by-nc-4.0-derivative-works/` as ignored.
- `git rev-list --objects main` should not include the old checked-in source path.

Suggested Enhancements (see `TODO.org`)
- Optional length-based splitting to target precise reading time per lesson.
- ZIP bundles for batch import convenience.
- Sanitization for external-link tracking parameters.
