set positional-arguments

derivative_dir := "cc-by-nc-4.0-derivative-works"
lesson_project := "lesson-material"
website_project := "website"
uv_cache_dir := ".uv-cache"
source := derivative_dir / "source/original/I promessi sposi Edizione semplificata.epub"
audio_dir := derivative_dir / "source/audio"
epub_dir := derivative_dir / "generated/epub"
html_dir := derivative_dir / "generated/html"
txt_dir := derivative_dir / "generated/txt"
epubcheck_bin := "/opt/local/bin/epubcheck"

default:
  @just --list

sync:
  UV_CACHE_DIR="{{uv_cache_dir}}" uv sync --project "{{lesson_project}}" --no-install-project --no-install-local
  UV_CACHE_DIR="{{uv_cache_dir}}" uv sync --project "{{website_project}}" --no-install-project --no-install-local

sync-lessons:
  UV_CACHE_DIR="{{uv_cache_dir}}" uv sync --project "{{lesson_project}}" --no-install-project --no-install-local

sync-website:
  UV_CACHE_DIR="{{uv_cache_dir}}" uv sync --project "{{website_project}}" --no-install-project --no-install-local

setup-worktree:
  just sync

prepare-source:
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.prepare_source "{{source}}"

import-audio: prepare-source
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.audio "{{source}}" "{{audio_dir}}"

lessons-epub: prepare-source
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.cli "{{source}}" "{{epub_dir}}"

lessons-html: prepare-source
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.cli "{{source}}" "{{html_dir}}" --format=html

lessons-txt: prepare-source
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.cli "{{source}}" "{{txt_dir}}" --format=txt

chapters-epub: prepare-source
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.cli "{{source}}" "{{epub_dir}}" --format=epub --by=chapters

check-epub:
  PYTHONPATH="{{lesson_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{lesson_project}}" --no-sync python -m promessi_lessons.check_epubs "{{epub_dir}}"

site: prepare-source
  PYTHONPATH="{{lesson_project}}:{{website_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{website_project}}" --no-sync python -m promessi_site.build

preview port="8000": site
  @echo ""
  @echo "Preview URL:"
  @echo "http://localhost:{{port}}/"
  @echo ""
  PYTHONPATH="{{website_project}}" UV_CACHE_DIR="{{uv_cache_dir}}" uv run --project "{{website_project}}" --no-sync python -m http.server "{{port}}" --directory "{{derivative_dir}}"

clean:
  rm -rf "{{derivative_dir}}/generated" "{{derivative_dir}}/index.html" "{{derivative_dir}}/site.css" "{{derivative_dir}}/.nojekyll" "{{derivative_dir}}/ATTRIBUTION.md"

clean-all:
  rm -rf "{{derivative_dir}}"

build: prepare-source
  just lessons-epub
  just lessons-html
  just lessons-txt
  just site
  just check-epub
