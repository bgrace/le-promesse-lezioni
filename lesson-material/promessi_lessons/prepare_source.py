from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


SOURCE_FILENAME = "I promessi sposi Edizione semplificata.epub"
CANONICAL_PATH = f"source/original/{SOURCE_FILENAME}"
LEGACY_PATH = f"source/{SOURCE_FILENAME}"
SOURCE_REFS = ("gh-pages", "origin/gh-pages")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy the canonical CC BY-NC source EPUB from the publication branch."
    )
    parser.add_argument("out_path", help="Local ignored destination for the source EPUB")
    return parser.parse_args()


def git_show(ref: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def find_source() -> tuple[str, str, bytes] | None:
    for ref in SOURCE_REFS:
        for path in (CANONICAL_PATH, LEGACY_PATH):
            data = git_show(ref, path)
            if data:
                return ref, path, data
    return None


def main() -> int:
    args = parse_args()
    out_path = Path(args.out_path)
    if out_path.exists():
        print(f"Source already exists at {out_path}")
        return 0

    found = find_source()
    if found is None:
        print(
            "Could not find the source EPUB on gh-pages or origin/gh-pages. "
            f"Expected {CANONICAL_PATH}.",
            file=sys.stderr,
        )
        return 2

    ref, source_path, data = found
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"Copied {ref}:{source_path} to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
