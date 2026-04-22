set positional-arguments

source := "source/I promessi sposi Edizione semplificata.epub"
epub_dir := "generated/lessons-epub"
html_dir := "generated/lessons-html"
txt_dir := "generated/lessons-txt"
chapters_epub_dir := "generated/chapters-epub"
epubcheck_bin := "/opt/local/bin/epubcheck"

default:
  @just --list

sync:
  uv sync

lessons-epub:
  .venv/bin/python3 split_chapters.py "{{source}}" "{{epub_dir}}"

lessons-html:
  .venv/bin/python3 split_chapters.py "{{source}}" "{{html_dir}}" --format=html

lessons-txt:
  .venv/bin/python3 split_chapters.py "{{source}}" "{{txt_dir}}" --format=txt

chapters-epub:
  .venv/bin/python3 split_chapters.py "{{source}}" "{{chapters_epub_dir}}" --by=chapters

check-epub:
  .venv/bin/python3 check_epubs.py "{{epub_dir}}"

clean:
  rm -rf generated

build:
  just lessons-epub
  just check-epub
