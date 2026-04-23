set positional-arguments

derivative_dir := "cc-by-nc-4.0-derivative-works"
source := derivative_dir / "source/original/I promessi sposi Edizione semplificata.epub"
epub_dir := derivative_dir / "generated/lessons-epub"
html_dir := derivative_dir / "generated/lessons-html"
txt_dir := derivative_dir / "generated/lessons-txt"
chapters_epub_dir := derivative_dir / "generated/chapters-epub"
epubcheck_bin := "/opt/local/bin/epubcheck"

default:
  @just --list

sync:
  uv venv
  uv sync

setup-worktree:
  just sync

prepare-source:
  .venv/bin/python3 prepare_source.py "{{source}}"

lessons-epub: prepare-source
  .venv/bin/python3 split_chapters.py "{{source}}" "{{epub_dir}}"

lessons-html: prepare-source
  .venv/bin/python3 split_chapters.py "{{source}}" "{{html_dir}}" --format=html

lessons-txt: prepare-source
  .venv/bin/python3 split_chapters.py "{{source}}" "{{txt_dir}}" --format=txt

chapters-epub: prepare-source
  .venv/bin/python3 split_chapters.py "{{source}}" "{{chapters_epub_dir}}" --by=chapters

check-epub:
  .venv/bin/python3 check_epubs.py "{{epub_dir}}"

site: prepare-source
  .venv/bin/python3 build_site.py

clean:
  rm -rf "{{derivative_dir}}/generated" "{{derivative_dir}}/index.html" "{{derivative_dir}}/site.css" "{{derivative_dir}}/.nojekyll" "{{derivative_dir}}/ATTRIBUTION.md"

clean-all:
  rm -rf "{{derivative_dir}}"

build: prepare-source
  just lessons-epub
  just lessons-html
  just lessons-txt
  just chapters-epub
  just site
  just check-epub
