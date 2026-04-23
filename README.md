# Le Promesse Lezioni

`le-promesse-lezioni` is a packaging and transformation project for study-oriented reuse of
*Leggiamo 102: I promessi sposi - edizione semplificata*, part of Andrea Petri's
Leggiamo! open educational resources.

The upstream material is published at <https://leggiamoitaliano.weebly.com/> and is presented
there as reusable teaching material under the Creative Commons Attribution-NonCommercial 4.0
International License. This repository's `main` branch contains only the Apache-2.0 code and
documentation needed to generate derived study artifacts. The CC BY-NC source EPUB and generated
artifacts live on the `gh-pages` publication branch and in local ignored build output.

## Project Intent

The practical goal is to turn a public teaching text that currently lives as a shared Google Doc
and EPUB into lesson-sized files that are easier to:

- import into LMS and language-reading platforms with file-size or text-length limits
- browse chapter by chapter or subsection by subsection
- read without unnecessary gloss clutter when hypertext lookup is already available
- preserve in multiple formats for different study preferences

The editorial transformations are intentionally modest:

- split the source into short subsection lessons
- also provide chapter-level exports where useful
- fix import-hostile formatting issues
- normalize or remove broken links and redirects
- strip page-break artifacts
- strip inline English glosses by default, with an option to preserve them

## Branch And License Model

This repo intentionally separates code from upstream-derived content.

- `main`: Apache-2.0 source code, docs, build scripts, and site generator only.
- `gh-pages`: CC BY-NC 4.0 publication branch containing the original source EPUB, generated
  lesson artifacts, static site files, and attribution notice.
- local output: ignored `cc-by-nc-4.0-derivative-works/` directory containing copied source and
  generated artifacts.

Users who check out only `main` should not receive a copy of the upstream-derived source EPUB or
generated lesson artifacts.

## Upstream Source

- Project site: <https://leggiamoitaliano.weebly.com/>
- Project framing: <https://leggiamoitaliano.weebly.com/this-project.html>
- Italian 102 page: <https://leggiamoitaliano.weebly.com/italian-102.html>
- Italian 102 readings doc:
  <https://docs.google.com/document/d/1kKUWgrMq1Q0Nv6dLQ91O1MpMdcYhuRdEpDlYN7MWmLg/edit?usp=sharing>
- Italian 102 audio folder:
  <https://drive.google.com/open?id=1TiD-6KvTX-qJQxcDTVanjvv2DaD6BjGQ>

## Local Build

Typical workflow:

```bash
just setup-worktree
just build
```

`just build` copies the canonical source EPUB from `gh-pages` into the ignored local directory,
then emits every generated format and the static website preview.

Generated local files go under:

```text
cc-by-nc-4.0-derivative-works/
```

The original source EPUB is copied to:

```text
cc-by-nc-4.0-derivative-works/source/original/I promessi sposi Edizione semplificata.epub
```

## Concrete Artifacts

The source currently yields:

- 16 chapter units
- 110 subsection lessons

The project emits these artifact families:

- lesson EPUBs: `cc-by-nc-4.0-derivative-works/generated/lessons-epub/`
- lesson HTML: `cc-by-nc-4.0-derivative-works/generated/lessons-html/`
- lesson TXT: `cc-by-nc-4.0-derivative-works/generated/lessons-txt/`
- chapter EPUBs: `cc-by-nc-4.0-derivative-works/generated/chapters-epub/`
- GitHub Pages site files: `cc-by-nc-4.0-derivative-works/index.html`, `site.css`, `.nojekyll`

## Other Commands

```bash
just prepare-source
just lessons-epub
just lessons-html
just lessons-txt
just chapters-epub
just site
just check-epub
just clean
```

`just clean` removes generated local artifacts and site files but leaves the copied source EPUB in
place. `just clean-all` removes the full ignored derivative directory.

## Attribution

Derived from Leggiamo! by Andrea Petri.

Upstream educational content is licensed under CC BY-NC 4.0:
<https://creativecommons.org/licenses/by-nc/4.0/>

This repository's source code is licensed separately under Apache License 2.0.
