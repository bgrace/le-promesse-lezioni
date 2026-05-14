from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

from promessi_lessons.paths import lesson_path
from promessi_lessons.source import SourceBundle
from promessi_lessons.xml import NS, parse_section_header_text, unwrap_google_redirect


DERIVATIVE_DIR = Path("cc-by-nc-4.0-derivative-works")
DEFAULT_AUDIO_DIR = DERIVATIVE_DIR / "source" / "audio"
GOOGLE_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id={file_id}"


@dataclass(frozen=True)
class AudioSource:
    chapter_number: int
    section_number: int
    title: str
    drive_file_id: str
    source_url: str
    path: str


@dataclass(frozen=True)
class AudioImportFailure:
    path: str
    drive_file_id: str
    error: str


def audio_relative_path(chapter_number: int, section_number: int, title: str) -> Path:
    return lesson_path("", chapter_number, section_number, title, "mp3")


def audio_path(audio_dir: str | Path, chapter_number: int, section_number: int, title: str) -> Path:
    return Path(audio_dir) / audio_relative_path(chapter_number, section_number, title)


def extract_drive_file_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in {"drive.google.com", "drive.usercontent.google.com"}:
        return None
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("id"):
        return query["id"][0]

    parts = [part for part in parsed.path.split("/") if part]
    if "d" in parts:
        index = parts.index("d")
        if index + 1 < len(parts):
            return parts[index + 1]
    return None


def section_audio_url(node) -> str | None:
    fallback = None
    for child in node.iter(f"{{{NS['x']}}}a"):
        href = child.attrib.get("href")
        if not href:
            continue
        url = unwrap_google_redirect(href)
        if extract_drive_file_id(url) is None:
            continue
        text = " ".join(child.itertext()).strip().upper()
        if text == "FILE AUDIO":
            return url
        fallback = fallback or url
    return fallback


def collect_audio_sources(src_path: str | Path, audio_dir: str | Path = DEFAULT_AUDIO_DIR) -> list[AudioSource]:
    source = SourceBundle.open(Path(src_path))
    try:
        root = source.parse_root()
        body = root.find("x:body", NS)
        if body is None:
            raise RuntimeError("Source EPUB did not contain an XHTML body.")

        audio_sources = []
        for node in body:
            section = parse_section_header_text(node)
            if section is None:
                continue
            chapter_number, section_number, title = section
            url = section_audio_url(node)
            if not url:
                continue
            drive_file_id = extract_drive_file_id(url)
            if not drive_file_id:
                continue
            path = audio_path(audio_dir, chapter_number, section_number, title)
            audio_sources.append(
                AudioSource(
                    chapter_number=chapter_number,
                    section_number=section_number,
                    title=title,
                    drive_file_id=drive_file_id,
                    source_url=url,
                    path=path.relative_to(audio_dir).as_posix(),
                )
            )
        return audio_sources
    finally:
        source.close()


def download_url(file_id: str) -> str:
    return GOOGLE_DOWNLOAD_URL.format(file_id=urllib.parse.quote(file_id))


def download_audio(audio: AudioSource, audio_dir: Path, *, force: bool = False) -> bool:
    destination = audio_dir / audio.path
    if destination.exists() and destination.stat().st_size > 0 and not force:
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        download_url(audio.drive_file_id),
        headers={"User-Agent": "promessi-lessons-audio-import/0.1"},
    )
    with urllib.request.urlopen(request) as response:
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("audio/"):
            raise RuntimeError(
                f"Expected audio for {audio.chapter_number}.{audio.section_number}, got {content_type!r}"
            )

        temp_path = destination.with_suffix(destination.suffix + ".part")
        with temp_path.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
        temp_path.replace(destination)
    return True


def write_manifest(
    audio_sources: list[AudioSource],
    audio_dir: Path,
    failures: list[AudioImportFailure] | None = None,
) -> None:
    manifest_path = audio_dir / "audio-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "audio": [asdict(audio) for audio in audio_sources],
                "failures": [asdict(failure) for failure in failures or []],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import public Google Drive audio files referenced by section headings."
    )
    parser.add_argument("src_path", help="Source EPUB or XHTML file")
    parser.add_argument(
        "audio_dir",
        nargs="?",
        default=str(DEFAULT_AUDIO_DIR),
        help="Ignored local output directory for imported audio",
    )
    parser.add_argument("--force", action="store_true", help="Re-download existing audio files")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any download fails")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_dir = Path(args.audio_dir)
    audio_sources = collect_audio_sources(args.src_path, audio_dir)
    if not audio_sources:
        print("No section audio links found.")
        return 1

    downloaded = 0
    skipped = 0
    failures = []
    for audio in audio_sources:
        try:
            changed = download_audio(audio, audio_dir, force=args.force)
        except (HTTPError, URLError, RuntimeError) as exc:
            failures.append(
                AudioImportFailure(
                    path=audio.path,
                    drive_file_id=audio.drive_file_id,
                    error=str(exc),
                )
            )
            print(f"Failed {audio.path}: {exc}", flush=True)
            continue

        if changed:
            downloaded += 1
            print(f"Downloaded {audio.path}", flush=True)
        else:
            skipped += 1
            print(f"Already exists {audio.path}", flush=True)

    write_manifest(audio_sources, audio_dir, failures)
    print(
        f"Done. {len(audio_sources)} audio links, {downloaded} downloaded, "
        f"{skipped} already present, {len(failures)} failed.",
        flush=True,
    )
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
