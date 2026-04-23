# Le Promesse Lezioni

`le-promesse-lezioni` is a packaging and transformation project for study-oriented reuse of
*Leggiamo 102: I promessi sposi - edizione semplificata*, part of Andrea Petri's
Leggiamo! open educational resources.

The upstream material is published at <https://leggiamoitaliano.weebly.com/> and is presented
there as reusable teaching material under the Creative Commons Attribution-NonCommercial 4.0
International License. This project does not attempt to replace the upstream work. Instead, it
reformats and republishes the Italian 102 content into cleaner, smaller, easier-to-import
artifacts for reading systems such as LingQ and similar language-learning workflows.

## Project Intent

The practical goal is to turn a public teaching text that currently lives as a shared Google Doc
and EPUB into lesson-sized files that are easier to:

- import into LMS and language-reading platforms with file-size or text-length limits
- browse chapter by chapter or subsection by subsection
- read without unnecessary gloss clutter when hypertext lookup is already available
- preserve in multiple formats for different study preferences

The editorial transformations in this repo are intentionally modest:

- split the source into short subsection lessons
- also provide chapter-level exports where useful
- fix import-hostile formatting issues
- normalize or remove broken links and redirects
- strip page-break artifacts
- optionally remove glosses that are less useful in hypertext reading environments

## Upstream Source

- Project site: <https://leggiamoitaliano.weebly.com/>
- Project framing: <https://leggiamoitaliano.weebly.com/this-project.html>
- Italian 102 page: <https://leggiamoitaliano.weebly.com/italian-102.html>
- Italian 102 readings doc:
  <https://docs.google.com/document/d/1kKUWgrMq1Q0Nv6dLQ91O1MpMdcYhuRdEpDlYN7MWmLg/edit?usp=sharing>
- Italian 102 audio folder:
  <https://drive.google.com/open?id=1TiD-6KvTX-qJQxcDTVanjvv2DaD6BjGQ>

## What This Repo Contains

This repository currently combines:

- source code for extracting, cleaning, and rendering lesson artifacts
- project documentation about the transformation pipeline and import targets
- a checked-in source EPUB used as the transformation input
- generated or planned lesson artifacts derived from the Italian 102 material

The checked-in source EPUB is:

- `source/I promessi sposi Edizione semplificata.epub`

## Concrete Artifacts

The source currently yields:

- 16 chapter units
- 110 subsection lessons

The project is designed to emit these artifact families:

### 1. Lesson EPUBs

One EPUB per subsection lesson.

- Output path: `generated/lessons-epub/`
- Filename pattern: `Capitolo-XX-YY.epub`
- Intended use: ebook readers, portable archives, LingQ-adjacent workflows

### 2. Lesson HTML

One minimal HTML document per subsection lesson.

- Output path: `generated/lessons-html/`
- Filename pattern: `Capitolo-XX-YY.html`
- Intended use: browser review, simple HTML import, visual QA

### 3. Lesson TXT

One plain-text file per subsection lesson.

- Output path: `generated/lessons-txt/`
- Filename pattern: `Capitolo-XX-YY.txt`
- Intended use: the most robust plain-text import path

### 4. Chapter EPUBs

One EPUB per chapter.

- Output path: `generated/chapters-epub/`
- Filename pattern: `Capitolo-XX.epub`
- Intended use: readers who prefer fewer, longer files

### 5. Planned Supporting Artifacts

Not all publishing surfaces necessarily exist yet, but the project is shaped to support them:

- ZIP bundles for batch download
- GitHub Pages browsing and artifact discovery
- audio-link placeholders or mirrors
- future lesson variants with alternate cleanup rules

## Current Transformation Rules

The exporter works from chapter and subsection headings in the source text:

- chapter headers like `Capitolo N`
- subsection headers like `N.M Title`

Section boundaries are taken directly from those markers. The project keeps the source numbering,
including irregularities, rather than renumbering the material into an artificial sequence.

## Why This Exists

The core value of the repo is not authorship of the original educational content. The value is in
making an already generous open educational resource easier to adopt, import, study, review, and
extend in modern reading systems.

In short:

- upstream provides the pedagogical adaptation
- this repo provides the transformation and packaging layer

## Local Commands

Typical commands:

```bash
just setup-worktree
just lessons-epub
just lessons-html
just lessons-txt
just chapters-epub
just site
```

## Attribution Note

Derived from Leggiamo! by Andrea Petri.

Upstream license notice:

- Creative Commons Attribution-NonCommercial 4.0 International License

When publishing derivative artifacts, keep upstream attribution and clearly describe the
transformations applied in this repository.
