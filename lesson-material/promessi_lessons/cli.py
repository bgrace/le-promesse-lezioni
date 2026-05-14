import argparse
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from promessi_lessons.audio import DEFAULT_AUDIO_DIR, audio_path
from promessi_lessons.extract import collect_chapters, collect_lessons
from promessi_lessons.paths import BOOK_TITLE, book_path, chapter_path, lesson_path
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
        choices=("all", "book", "sections", "chapters"),
        default="all",
        help="Write the whole book, sections, chapters, or the full collection",
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
    return os.path.join(DERIVATIVE_DIR, "generated", out_format)


def make_section_content(lesson):
    chapter_header = ET.Element(f"{{{NS['x']}}}h1")
    chapter_header.text = f"Capitolo {lesson.chapter_number}"
    section_header = ET.Element(f"{{{NS['x']}}}h2")
    section_header.text = (
        f"{lesson.chapter_number}.{lesson.section_number} {lesson.title}".strip()
    )
    return [chapter_header, section_header] + lesson.nodes


def add_audio_to_section_content(content_nodes, lesson, out_path):
    source_path = audio_path(
        DEFAULT_AUDIO_DIR,
        lesson.chapter_number,
        lesson.section_number,
        lesson.title,
    )
    if not source_path.exists():
        return content_nodes

    href = os.path.relpath(source_path, Path(out_path).parent).replace(os.sep, "/")
    container = ET.Element(f"{{{NS['x']}}}div", attrib={"class": "lesson-audio"})
    audio = ET.SubElement(
        container,
        f"{{{NS['x']}}}audio",
        attrib={"controls": "controls", "preload": "metadata", "src": href},
    )
    fallback = ET.SubElement(audio, f"{{{NS['x']}}}a", attrib={"href": href})
    fallback.text = "Audio"
    download = ET.SubElement(container, f"{{{NS['x']}}}p")
    link = ET.SubElement(download, f"{{{NS['x']}}}a", attrib={"href": href})
    link.text = "Audio MP3"
    return [*content_nodes[:2], container, *content_nodes[2:]]


def chapter_display_title(chapter):
    if chapter.title:
        return f"Capitolo {chapter.number} - {chapter.title}"
    return f"Capitolo {chapter.number}"


def make_chapter_content(chapter):
    if not chapter.title:
        return chapter.nodes
    chapter_header = ET.Element(f"{{{NS['x']}}}h1")
    chapter_header.text = chapter_display_title(chapter)
    return [chapter_header] + chapter.nodes[1:]


def write_book_output(nodes, out_dir, out_format, source, args):
    title_text = BOOK_TITLE

    if out_format == "html":
        out_path = book_path(out_dir, out_format)
        write_html(
            out_path,
            title_text,
            nodes,
            source,
            strip_english_annotations=args.strip_english_annotations,
        )
    elif out_format == "txt":
        out_path = book_path(out_dir, out_format)
        state = build_render_state(
            title_text,
            nodes,
            source,
            image_prefix="images",
            strip_english_annotations=args.strip_english_annotations,
        )
        write_text(out_path, flatten_text(state.nodes))
    else:
        out_path = book_path(out_dir, out_format)
        write_epub(
            out_path,
            title_text,
            nodes,
            source,
            strip_english_annotations=args.strip_english_annotations,
        )

    print(f"Wrote {out_path}")
    return 1


def write_chapter_outputs(chapters, out_dir, out_format, source, args):
    count = 0
    for chapter in chapters:
        title_text = chapter_display_title(chapter)
        content_nodes = make_chapter_content(chapter)

        if out_format == "html":
            out_path = chapter_path(out_dir, chapter.number, out_format)
            write_html(
                out_path,
                title_text,
                content_nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )
        elif out_format == "txt":
            out_path = chapter_path(out_dir, chapter.number, out_format)
            state = build_render_state(
                title_text,
                content_nodes,
                source,
                image_prefix="images",
                strip_english_annotations=args.strip_english_annotations,
            )
            write_text(out_path, flatten_text(state.nodes))
        else:
            out_path = chapter_path(out_dir, chapter.number, out_format)
            write_epub(
                out_path,
                title_text,
                content_nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )

        count += 1
        print(f"Wrote {out_path}")

    return count


def write_section_outputs(lessons, out_dir, out_format, source, args):
    count = 0
    for lesson in lessons:
        content_nodes = make_section_content(lesson)
        title_text = (
            f"Capitolo {lesson.chapter_number} - "
            f"{lesson.chapter_number}.{lesson.section_number} {lesson.title}"
        ).strip()

        if out_format == "html":
            out_path = lesson_path(
                out_dir,
                lesson.chapter_number,
                lesson.section_number,
                lesson.title,
                out_format,
            )
            content_nodes = add_audio_to_section_content(content_nodes, lesson, out_path)
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
            out_path = lesson_path(
                out_dir,
                lesson.chapter_number,
                lesson.section_number,
                lesson.title,
                out_format,
            )
            write_text(out_path, parts)
        else:
            out_path = lesson_path(
                out_dir,
                lesson.chapter_number,
                lesson.section_number,
                lesson.title,
                out_format,
            )
            write_epub(
                out_path,
                title_text,
                content_nodes,
                source,
                strip_english_annotations=args.strip_english_annotations,
            )

        count += 1
        print(f"Wrote {out_path}")

    return count


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

        chapters = collect_chapters(nodes)
        if args.by in {"all", "chapters"} and not chapters:
            print(
                "No chapters found. Looked for headings starting 'Capitolo '",
                file=sys.stderr,
            )
            sys.exit(4)

        if args.by == "book":
            count = write_book_output(nodes, out_dir, args.format, source, args)
            print(f"Done. Wrote {count} files to {out_dir}")
            return

        if args.by == "chapters":
            count = write_chapter_outputs(chapters, out_dir, args.format, source, args)
            print(f"Done. Wrote {count} files to {out_dir}")
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

        if args.by == "sections":
            count = write_section_outputs(lessons, out_dir, args.format, source, args)
            print(f"Done. Wrote {count} files to {out_dir}")
            return

        count = 0
        count += write_book_output(nodes, out_dir, args.format, source, args)
        count += write_chapter_outputs(chapters, out_dir, args.format, source, args)
        count += write_section_outputs(lessons, out_dir, args.format, source, args)
        print(f"Done. Wrote {count} files to {out_dir}")
    finally:
        source.close()


if __name__ == "__main__":
    main()
