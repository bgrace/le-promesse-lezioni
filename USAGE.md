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

## Individual Steps

```bash
just prepare-source
just lessons-epub
just lessons-html
just lessons-txt
just chapters-epub
just site
just check-epub
```

The copied source EPUB is:

```text
cc-by-nc-4.0-derivative-works/source/original/I promessi sposi Edizione semplificata.epub
```

Generated files go under:

```text
cc-by-nc-4.0-derivative-works/generated/
```

## Code Layout

- `source.py` reads EPUB or XHTML input
- `extract.py` finds chapters and numbered lessons
- `transforms.py` runs cleanup passes before rendering
- `render.py` writes EPUB, HTML, and TXT output
- `cli.py` keeps the command surface thin
- `build_site.py` renders the GitHub Pages publication site into the ignored derivative directory
- `prepare_source.py` copies the canonical source EPUB from `gh-pages`

## Annotation Cleanup

By default the pipeline strips inline English glosses such as `rammarico (= regret)`. Use
`--keep-english-annotations` to preserve them.

## LingQ Note

The exporter is designed around shorter subsection lessons because LingQ imports and review
sessions are more manageable at that size.
