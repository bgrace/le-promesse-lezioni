#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import os
import subprocess
import sys


EPUBCHECK_BIN = "/opt/local/bin/epubcheck"
DEFAULT_EPUB_DIR = Path("generated/lessons-epub")
MAX_WORKERS = max(1, min(16, os.cpu_count() or 1))


def check(path: Path):
    proc = subprocess.run(
        [EPUBCHECK_BIN, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return path, proc.returncode, proc.stdout


def main():
    parser = argparse.ArgumentParser(description="Validate a directory of EPUB files with epubcheck.")
    parser.add_argument("epub_dir", nargs="?", default=str(DEFAULT_EPUB_DIR))
    args = parser.parse_args()

    epub_dir = Path(args.epub_dir)
    files = sorted(epub_dir.glob("*.epub"))
    if not files:
        print(f"No EPUB files found under {epub_dir}", file=sys.stderr)
        return 1

    failures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(check, path): path for path in files}
        for future in as_completed(futures):
            path, rc, out = future.result()
            if rc != 0:
                failures.append((path, rc, out))

    if failures:
        path, rc, out = failures[0]
        print(f"FAIL {path}")
        print(out)
        return rc

    print(f"validated {len(files)} epubs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
