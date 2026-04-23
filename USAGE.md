# I promessi sposi lesson exporter

Small utilities for turning the checked-in source EPUB into LingQ-sized lessons.

## Quick start

```bash
just sync
just lessons-epub
just check-epub
```

Those commands install the local environment, emit one EPUB per subsection, and validate the generated files with `epubcheck`.

The code is split into focused modules under `promessi_lessons/`:
- `source.py` reads EPUB or XHTML input
- `extract.py` finds chapters and numbered lessons
- `transforms.py` runs cleanup passes before rendering
- `render.py` writes EPUB, HTML, and TXT output
- `cli.py` keeps the command surface thin

## Other formats

```bash
just lessons-html
just lessons-txt
just chapters-epub
just clean
```

The checked-in source lives at `source/I promessi sposi Edizione semplificata.epub`.
Generated files go under `generated/` and are ignored by git.

If you want the raw command, `uv run python3 split_chapters.py "source/I promessi sposi Edizione semplificata.epub" generated/lessons-epub` is the default exporter invocation.

By default the pipeline strips inline English glosses such as `rammarico (= regret)`. Use `--keep-english-annotations` to preserve them.

## LingQ note

The exporter is designed around shorter subsection lessons because LingQ imports and review sessions are more manageable at that size.
