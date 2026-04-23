from promessi_lessons.model import Chapter, Lesson
from promessi_lessons.xml import parse_chapter_header_number, parse_section_header_text


def collect_chapters(nodes):
    chapters = []
    current_nodes = []
    current_ch_num = None

    for node in nodes:
        chapter_number = parse_chapter_header_number(node)
        if chapter_number is not None:
            if current_ch_num is not None:
                chapters.append(Chapter(number=current_ch_num, nodes=current_nodes))
                current_nodes = []

            current_ch_num = chapter_number
            current_nodes.append(node)
            continue

        if current_ch_num is not None:
            current_nodes.append(node)

    if current_ch_num is not None and current_nodes:
        chapters.append(Chapter(number=current_ch_num, nodes=current_nodes))

    return chapters


def collect_lessons(nodes):
    lessons = []
    warnings = []
    current_ch = None
    current_sec = None
    current_nodes = []
    current_sec_title = ""
    expected_ch = 1
    expected_sec = 1

    def flush_current():
        nonlocal current_nodes, current_sec, current_sec_title
        if current_ch is not None and current_sec is not None and current_nodes:
            lessons.append(
                Lesson(
                    chapter_number=current_ch,
                    section_number=current_sec,
                    title=current_sec_title,
                    nodes=current_nodes,
                )
            )
        current_nodes = []
        current_sec = None
        current_sec_title = ""

    for node in nodes:
        chapter_number = parse_chapter_header_number(node)
        if chapter_number is not None:
            flush_current()
            if chapter_number != expected_ch:
                warnings.append(
                    f"Expected chapter {expected_ch}, found chapter {chapter_number}"
                )
            current_ch = chapter_number
            expected_ch = chapter_number + 1
            expected_sec = 1
            continue

        sec_info = parse_section_header_text(node)
        if sec_info is not None:
            ch_no_in_header, sec_no, title_rest = sec_info
            if current_ch is None:
                warnings.append(
                    f"Found section {ch_no_in_header}.{sec_no} before any chapter header"
                )
                current_ch = ch_no_in_header
                expected_ch = max(expected_ch, current_ch + 1)
                expected_sec = 1
            elif ch_no_in_header != current_ch:
                flush_current()
                warnings.append(
                    f"Expected section in chapter {current_ch}, found {ch_no_in_header}.{sec_no}"
                )
                current_ch = ch_no_in_header
                expected_ch = max(expected_ch, current_ch + 1)
                expected_sec = 1

            if sec_no != expected_sec:
                warnings.append(
                    f"Expected section {current_ch}.{expected_sec}, found {current_ch}.{sec_no}"
                )

            flush_current()
            current_sec = sec_no
            current_sec_title = (
                title_rest if title_rest else f"Sezione {current_ch}.{current_sec}"
            )
            expected_sec = sec_no + 1
            continue

        if current_ch is not None and current_sec is not None:
            current_nodes.append(node)

    flush_current()
    return lessons, warnings

