import argparse
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from promessi_lessons.extract import collect_chapters, collect_lessons
from promessi_lessons.render import (
    build_render_state,
    flatten_text,
    write_epub,
    write_html,
    write_text,
)
from promessi_lessons.source import SourceBundle
from promessi_lessons.xml import NS

DERIVATIVE_DIR = "cc-by-nc-4.0-derivative-works"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Split the source XHTML or EPUB into lesson-sized exports."
    )
    parser.add_argument("src_path", help="Source EPUB or XHTML file")
    parser.add_argument(
        "out_dir",
        nargs="?",
        help="Output directory (defaults to generated/<mode>-<format>)",
    )
    parser.add_argument(
        "--by",
        choices=("sections", "chapters"),
        default="sections",
        help="Split output into one file per section or per chapter",
    )
    parser.add_argument(
        "--format",
        choices=("epub", "html", "txt"),
        default="epub",
        help="Output format for each lesson",
    )
    parser.add_argument(
        "--strip-english-annotations",
        dest="strip_english_annotations",
        action="store_true",
        default=True,
        help="Remove inline English glosses like '(= priest)' from the output",
    )
    parser.add_argument(
        "--keep-english-annotations",
        dest="strip_english_annotations",
        action="store_false",
        help="Keep inline English glosses in the output",
    )
    return parser.parse_args()


def default_out_dir(by, out_format):
    prefix = "chapters" if by == "chapters" else "lessons"
    return os.path.join(DERIVATIVE_DIR, "generated", f"{prefix}-{out_format}")


def make_section_content(lesson):
    chapter_header = ET.Element(f"{{{NS['x']}}}h1")
    chapter_header.text = f"Capitolo {lesson.chapter_number}"
    section_header = ET.Element(f"{{{NS['x']}}}h2")
    section_header.text = (
        f"{lesson.chapter_number}.{lesson.section_number} {lesson.title}".strip()
    )
    return [chapter_header, section_header] + lesson.nodes


def write_chapter_outputs(chapters, out_dir, out_format, source, args):
    count = 0
    for chapter in chapters:
        name_num = f"{chapter.number:02d}"
        title_text = f"Capitolo {chapter.number}"

        if out_format == "html":
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.html")
            write_html(
                out_path,
                title_text,
                chapter.nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )
        elif out_format == "txt":
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.txt")
            state = build_render_state(
                title_text,
                chapter.nodes,
                source,
                image_prefix="images",
                strip_english_annotations=args.strip_english_annotations,
            )
            write_text(out_path, flatten_text(state.nodes))
        else:
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.epub")
            write_epub(
                out_path,
                title_text,
                chapter.nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )

        count += 1
        print(f"Wrote {out_path}")

    print(f"Done. Wrote {count} files to {out_dir}")


def write_section_outputs(lessons, out_dir, out_format, source, args):
    count = 0
    for lesson in lessons:
        content_nodes = make_section_content(lesson)
        name_ch = f"{lesson.chapter_number:02d}"
        name_sec = f"{lesson.section_number:02d}"
        title_text = (
            f"Capitolo {lesson.chapter_number} - "
            f"{lesson.chapter_number}.{lesson.section_number} {lesson.title}"
        ).strip()

        if out_format == "html":
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.html")
            write_html(
                out_path,
                title_text,
                content_nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )
        elif out_format == "txt":
            state = build_render_state(
                title_text,
                content_nodes,
                source,
                image_prefix="images",
                strip_english_annotations=args.strip_english_annotations,
            )
            text_nodes = state.nodes[2:]
            parts = [
                f"Capitolo {lesson.chapter_number}",
                f"{lesson.chapter_number}.{lesson.section_number} {lesson.title}".strip(),
                *flatten_text(text_nodes),
            ]
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.txt")
            write_text(out_path, parts)
        else:
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.epub")
            write_epub(
                out_path,
                title_text,
                content_nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )

        count += 1
        print(f"Wrote {out_path}")

    print(f"Done. Wrote {count} files to {out_dir}")


def main():
    args = parse_args()
    src_path = Path(args.src_path)
    out_dir = args.out_dir or default_out_dir(args.by, args.format)
    os.makedirs(out_dir, exist_ok=True)

    ET.register_namespace("", NS["x"])

    source = SourceBundle.open(src_path)
    try:
        root = source.parse_root()
        body = root.find("x:body", NS)
        if body is None:
            print("No <body> found; aborting", file=sys.stderr)
            sys.exit(3)

        nodes = list(body)

        if args.by == "chapters":
            chapters = collect_chapters(nodes)
            if not chapters:
                print(
                    "No chapters found. Looked for headings starting 'Capitolo '",
                    file=sys.stderr,
                )
                sys.exit(4)
            write_chapter_outputs(chapters, out_dir, args.format, source, args)
            return

        lessons, warnings = collect_lessons(nodes)
        if not lessons:
            print(
                "No sections found. Looked for numbered section headings like '1.1 Title'",
                file=sys.stderr,
            )
            sys.exit(5)

        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        write_section_outputs(lessons, out_dir, args.format, source, args)
    finally:
        source.close()
