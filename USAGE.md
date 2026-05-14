# I promessi sposi lesson exporter

Small utilities for turning the Leggiamo! Italian 102 source EPUB into LingQ-sized lessons.

The `main` branch does not track the source EPUB or generated derived works. Those CC BY-NC 4.0
materials are copied from the `gh-pages` publication branch into the ignored local directory
`cc-by-nc-4.0-derivative-works/`.

## Quick Start

```bash
just setup-worktree
just build
```

Those commands install the local environment, copy the canonical source EPUB from `gh-pages`, emit
all lesson formats, build the static site files, and validate generated EPUBs with `epubcheck`.

The repo contains two uv projects:

- `lesson-material/`: source copy, lesson export, and EPUB validation commands
- `website/`: static site generation and site assets

## Individual Steps

```bash
just sync-lessons
just sync-website
just prepare-source
just import-audio
just lessons-epub
just lessons-html
just lessons-txt
just chapters-epub
just site
just preview
just check-epub
```

The `lessons-*` commands emit a complete collection for that format: whole book, chapter files,
and section files.

`just import-audio` downloads the public MP3 files linked from section headings into
`cc-by-nc-4.0-derivative-works/source/audio/`. Rebuild HTML lessons after importing audio to add
per-section audio controls, and rebuild the site to expose catalog `AUDIO` links.

Published audio is served directly from `source/audio/` on the `gh-pages` branch, not from Git LFS,
so the static site can serve MP3s without relying on the upstream Drive links.

Use `just preview` to rebuild the static site, print a clickable local URL, and serve the ignored
derivative directory at <http://localhost:8000/>. Use `just preview 8080` to choose another port.

The copied source EPUB is:

```text
cc-by-nc-4.0-derivative-works/source/original/I promessi sposi Edizione semplificata.epub
```

Generated files go under:

```text
cc-by-nc-4.0-derivative-works/generated/
```

Each format has its own directory:

```text
cc-by-nc-4.0-derivative-works/generated/epub/
cc-by-nc-4.0-derivative-works/generated/html/
cc-by-nc-4.0-derivative-works/generated/txt/
```

Inside each format directory, the layout is:

```text
I-promessi-sposi-Edizione-semplificata.<format>
Capitolo-01.<format>
Capitolo-01/01-01-Don-Abbondio.<format>
```

## Code Layout

- `lesson-material/promessi_lessons/source.py` reads EPUB or XHTML input
- `lesson-material/promessi_lessons/extract.py` finds chapters and numbered lessons
- `lesson-material/promessi_lessons/paths.py` centralizes generated artifact naming
- `lesson-material/promessi_lessons/transforms.py` runs cleanup passes before rendering
- `lesson-material/promessi_lessons/render.py` writes EPUB, HTML, and TXT output
- `lesson-material/promessi_lessons/cli.py` keeps the lesson command surface thin
- `lesson-material/promessi_lessons/prepare_source.py` copies the canonical source EPUB from `gh-pages`
- `website/promessi_site/build.py` renders the GitHub Pages publication site into the ignored derivative directory
- `website/promessi_site/resources/site.css` is the source stylesheet copied into the publication output
- `website/promessi_site/resources/templates/` contains the static site templates

## Annotation Cleanup

By default the pipeline strips inline English glosses such as `rammarico (= regret)`. Use
`--keep-english-annotations` to preserve them.

The pipeline also strips source `FILE AUDIO` links from generated products until there is a
deliberate audio hosting strategy. Imported local audio is linked back into section-level HTML
lessons separately.

## LingQ Note

The exporter is designed around shorter subsection lessons because LingQ imports and review
sessions are more manageable at that size.
