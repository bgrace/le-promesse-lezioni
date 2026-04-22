#!/usr/bin/env python3
import argparse
import os
import posixpath
import re
import sys
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path, PurePosixPath


NS = {"x": "http://www.w3.org/1999/xhtml"}
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}
XML_NS = "http://www.w3.org/XML/1998/namespace"
EPUB_NS = "http://www.idpf.org/2007/ops"
SEC_RE = re.compile(r"^(\d+)\.(\d+)\b(.*)")
CHAPTER_RE = re.compile(r"^Capitolo\s+(\d+)\b")
HEADING_TAGS = {f"{{{NS['x']}}}h1", f"{{{NS['x']}}}h2", f"{{{NS['x']}}}h3"}


def itertext(el):
    return "".join(el.itertext()) if el is not None else ""


def is_chapter_header(elem) -> bool:
    return parse_chapter_header_number(elem) is not None


def parse_chapter_header_number(elem):
    if elem is None or elem.tag not in HEADING_TAGS:
        return None
    match = CHAPTER_RE.match(itertext(elem).strip())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def parse_section_header_text(elem):
    if elem is None or elem.tag not in HEADING_TAGS:
        return None
    match = SEC_RE.match(itertext(elem).strip())
    if not match:
        return None
    ch_s, sec_s, rest = match.groups()
    try:
        return int(ch_s), int(sec_s), (rest or "").strip()
    except ValueError:
        return None


def deepcopy(elem):
    new = ET.Element(elem.tag, attrib=dict(elem.attrib))
    new.text = elem.text
    new.tail = elem.tail
    for child in list(elem):
        new.append(deepcopy(child))
    return new


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
    return parser.parse_args()


class SourceBundle:
    def __init__(self, src_path: Path):
        self.src_path = Path(src_path)
        self.archive = None
        self.xhtml_member = None
        self.xhtml_bytes = None
        self.base_dir = None
        self.base_path = None
        self.is_archive = False

    @classmethod
    def open(cls, src_path):
        bundle = cls(Path(src_path))
        if bundle.src_path.suffix.lower() == ".epub":
            bundle._open_epub()
        else:
            bundle._open_xhtml()
        return bundle

    def _open_xhtml(self):
        self.xhtml_bytes = self.src_path.read_bytes()
        self.base_path = self.src_path.resolve().parent

    def _open_epub(self):
        self.is_archive = True
        self.archive = zipfile.ZipFile(self.src_path)
        opf_path = self._find_rootfile_path()
        self.xhtml_member = self._find_primary_xhtml_member(opf_path)
        self.xhtml_bytes = self.archive.read(self.xhtml_member)
        self.base_dir = posixpath.dirname(self.xhtml_member)

    def _find_rootfile_path(self):
        container_root = ET.fromstring(self.archive.read("META-INF/container.xml"))
        rootfile = container_root.find("c:rootfiles/c:rootfile", CONTAINER_NS)
        if rootfile is None:
            raise RuntimeError("EPUB container.xml does not declare a rootfile")
        full_path = rootfile.attrib.get("full-path")
        if not full_path:
            raise RuntimeError("EPUB rootfile entry is missing full-path")
        return full_path

    def _find_primary_xhtml_member(self, opf_path):
        opf_root = ET.fromstring(self.archive.read(opf_path))
        manifest = {}
        for item in opf_root.findall("opf:manifest/opf:item", OPF_NS):
            item_id = item.attrib.get("id")
            if item_id:
                manifest[item_id] = item.attrib

        opf_dir = posixpath.dirname(opf_path)
        spine = opf_root.find("opf:spine", OPF_NS)
        if spine is None:
            raise RuntimeError("EPUB package.opf does not define a spine")

        for itemref in spine.findall("opf:itemref", OPF_NS):
            item_id = itemref.attrib.get("idref")
            item = manifest.get(item_id, {})
            media_type = item.get("media-type")
            properties = item.get("properties", "")
            href = item.get("href")
            if not href or "nav" in properties.split():
                continue
            if media_type in {"application/xhtml+xml", "text/html"}:
                return posixpath.normpath(posixpath.join(opf_dir, href))

        raise RuntimeError("Could not locate a primary XHTML document in the EPUB spine")

    def parse_root(self):
        return ET.fromstring(self.xhtml_bytes)

    def resolve_local_ref(self, reference):
        if self.is_archive:
            return posixpath.normpath(posixpath.join(self.base_dir, reference))
        return str((self.base_path / Path(reference)).resolve())

    def read_local_ref(self, reference):
        resolved = self.resolve_local_ref(reference)
        if self.is_archive:
            return self.archive.read(resolved)
        return Path(resolved).read_bytes()

    def close(self):
        if self.archive is not None:
            self.archive.close()


def default_out_dir(by, out_format):
    prefix = "chapters" if by == "chapters" else "lessons"
    return os.path.join("generated", f"{prefix}-{out_format}")


def make_doc_minimal(title_text, nodes):
    html = ET.Element(
        f"{{{NS['x']}}}html",
        attrib={
            f"{{{XML_NS}}}lang": "it",
            "lang": "it",
        },
    )
    head = ET.SubElement(html, f"{{{NS['x']}}}head")
    title = ET.SubElement(head, f"{{{NS['x']}}}title")
    title.text = title_text
    ET.SubElement(head, f"{{{NS['x']}}}meta", attrib={"charset": "UTF-8"})
    body = ET.SubElement(html, f"{{{NS['x']}}}body")
    for node in nodes:
        body.append(node)
    return html


def make_epub_content_doc(title_text, nodes):
    html = ET.Element(
        f"{{{NS['x']}}}html",
        attrib={
            f"{{{XML_NS}}}lang": "it",
            "lang": "it",
            "xmlns:epub": EPUB_NS,
        },
    )
    head = ET.SubElement(html, f"{{{NS['x']}}}head")
    title = ET.SubElement(head, f"{{{NS['x']}}}title")
    title.text = title_text
    ET.SubElement(head, f"{{{NS['x']}}}meta", attrib={"charset": "UTF-8"})
    ET.SubElement(
        head,
        f"{{{NS['x']}}}link",
        attrib={
            "rel": "stylesheet",
            "type": "text/css",
            "href": "../styles/lesson.css",
        },
    )
    body = ET.SubElement(html, f"{{{NS['x']}}}body")
    for node in nodes:
        body.append(node)
    return html


def serialize_xml(elem):
    return ET.tostring(elem, encoding="utf-8", xml_declaration=True, method="xml")


def unwrap_google_redirect(url):
    if not url:
        return url
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != "www.google.com" or parsed.path != "/url":
        return url
    query = urllib.parse.parse_qs(parsed.query)
    target = query.get("q", [None])[0]
    return target or url


def media_type_for_path(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        ".css": "text/css",
        ".gif": "image/gif",
        ".html": "text/html",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".xhtml": "application/xhtml+xml",
    }.get(ext, "application/octet-stream")


def is_local_reference(reference):
    return bool(reference) and not reference.startswith(
        ("http://", "https://", "/", "data:", "mailto:")
    )


def prepare_rich_nodes(nodes, source, image_prefix, strip_pagebreaks):
    container = ET.Element(f"{{{NS['x']}}}div")
    for node in nodes:
        container.append(node)

    asset_blobs = {}
    asset_names = {}

    def ensure_asset_name(reference):
        resolved = source.resolve_local_ref(reference)
        if resolved in asset_names:
            return asset_names[resolved]

        base = PurePosixPath(reference).name or PurePosixPath(resolved).name
        stem, ext = os.path.splitext(base)
        candidate = base
        index = 2
        while candidate in asset_blobs and asset_blobs[candidate][0] != resolved:
            candidate = f"{stem}-{index}{ext}"
            index += 1
        data = source.read_local_ref(reference)
        asset_blobs[candidate] = (resolved, data)
        asset_names[resolved] = candidate
        return candidate

    if strip_pagebreaks:
        parent_map = {child: parent for parent in container.iter() for child in parent}
        for child in list(container.iter()):
            if child.tag == f"{{{NS['x']}}}hr":
                parent = parent_map.get(child)
                if parent is not None:
                    parent.remove(child)

    ids_in_document = {
        child.attrib["id"]
        for child in container.iter()
        if child.attrib.get("id")
    }

    for child in container.iter():
        if child.tag == f"{{{NS['x']}}}a":
            href = child.attrib.get("href")
            if href:
                rewritten_href = unwrap_google_redirect(href)
                if rewritten_href.startswith("#") and rewritten_href[1:] not in ids_in_document:
                    child.attrib.pop("href", None)
                else:
                    child.set("href", rewritten_href)

        if child.tag != f"{{{NS['x']}}}img":
            continue

        src = child.attrib.get("src")
        if not is_local_reference(src):
            continue

        try:
            asset_name = ensure_asset_name(src)
        except (FileNotFoundError, KeyError):
            continue

        child.set("src", f"{image_prefix}/{asset_name}")
        if not child.attrib.get("alt"):
            child.set("alt", os.path.splitext(asset_name)[0])

    return list(container), {name: data for name, (_, data) in asset_blobs.items()}


def build_package_opf(title_text, identifier, manifest_items):
    manifest_lines = []
    for item in manifest_items:
        extra = (
            f' properties="{escape(item["properties"], quote=True)}"'
            if item.get("properties")
            else ""
        )
        manifest_lines.append(
            f'    <item id="{escape(item["id"], quote=True)}" '
            f'href="{escape(item["href"], quote=True)}" '
            f'media-type="{escape(item["media_type"], quote=True)}"{extra}/>'
        )

    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="bookid">urn:uuid:{escape(identifier)}</dc:identifier>\n'
        f'    <dc:title>{escape(title_text)}</dc:title>\n'
        '    <dc:language>it</dc:language>\n'
        f'    <meta property="dcterms:modified">{modified}</meta>\n'
        "  </metadata>\n"
        "  <manifest>\n"
        + "\n".join(manifest_lines)
        + "\n"
        "  </manifest>\n"
        "  <spine>\n"
        '    <itemref idref="content"/>\n'
        "  </spine>\n"
        "</package>\n"
    ).encode("utf-8")


def build_nav_doc(title_text):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="it" lang="it">\n'
        "  <head>\n"
        f"    <title>{escape(title_text)}</title>\n"
        '    <meta charset="UTF-8"/>\n'
        "  </head>\n"
        "  <body>\n"
        '    <nav epub:type="toc" id="toc">\n'
        f"      <h1>{escape(title_text)}</h1>\n"
        "      <ol>\n"
        f'        <li><a href="text/lesson.xhtml">{escape(title_text)}</a></li>\n'
        "      </ol>\n"
        "    </nav>\n"
        "  </body>\n"
        "</html>\n"
    ).encode("utf-8")


def build_container_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>\n"
    ).encode("utf-8")


def epub_css():
    return (
        "body {\n"
        "  font-family: serif;\n"
        "  line-height: 1.55;\n"
        "  margin: 5%;\n"
        "}\n"
        "h1, h2 {\n"
        "  line-height: 1.2;\n"
        "}\n"
        "h1 {\n"
        "  font-size: 1.7em;\n"
        "  margin: 0 0 0.35em;\n"
        "}\n"
        "h2 {\n"
        "  font-size: 1.2em;\n"
        "  margin: 0 0 1em;\n"
        "  color: #444;\n"
        "}\n"
        "p, ul, ol, blockquote {\n"
        "  margin: 0 0 1em;\n"
        "}\n"
        "img {\n"
        "  display: block;\n"
        "  max-width: 100%;\n"
        "  height: auto;\n"
        "  margin: 1em auto;\n"
        "}\n"
        "a {\n"
        "  color: #0b5394;\n"
        "}\n"
    ).encode("utf-8")


def write_html(out_path, title_text, content_nodes, source):
    html_nodes, asset_blobs = prepare_rich_nodes(
        content_nodes,
        source,
        image_prefix="images",
        strip_pagebreaks=True,
    )
    doc = make_doc_minimal(title_text, html_nodes)
    ET.ElementTree(doc).write(out_path, encoding="utf-8", xml_declaration=True, method="xml")

    if asset_blobs:
        images_dir = Path(out_path).parent / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for asset_name, data in asset_blobs.items():
            (images_dir / asset_name).write_bytes(data)


def write_epub(out_path, title_text, content_nodes, source):
    content_nodes, asset_blobs = prepare_rich_nodes(
        content_nodes,
        source,
        image_prefix="../images",
        strip_pagebreaks=True,
    )
    content_doc = serialize_xml(make_epub_content_doc(title_text, content_nodes))
    nav_doc = build_nav_doc(title_text)
    manifest_items = [
        {
            "id": "nav",
            "href": "nav.xhtml",
            "media_type": "application/xhtml+xml",
            "properties": "nav",
        },
        {
            "id": "content",
            "href": "text/lesson.xhtml",
            "media_type": "application/xhtml+xml",
        },
        {
            "id": "css",
            "href": "styles/lesson.css",
            "media_type": "text/css",
        },
    ]

    for index, asset_name in enumerate(sorted(asset_blobs), start=1):
        manifest_items.append(
            {
                "id": f"asset{index}",
                "href": f"images/{asset_name}",
                "media_type": media_type_for_path(asset_name),
            }
        )

    package_opf = build_package_opf(title_text, str(uuid.uuid4()), manifest_items)

    with zipfile.ZipFile(out_path, "w") as zf:
        zf.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            build_container_xml(),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        zf.writestr("OEBPS/package.opf", package_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav_doc, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr(
            "OEBPS/text/lesson.xhtml",
            content_doc,
            compress_type=zipfile.ZIP_DEFLATED,
        )
        zf.writestr(
            "OEBPS/styles/lesson.css",
            epub_css(),
            compress_type=zipfile.ZIP_DEFLATED,
        )
        for asset_name, data in sorted(asset_blobs.items()):
            zf.writestr(
                f"OEBPS/images/{asset_name}",
                data,
                compress_type=zipfile.ZIP_DEFLATED,
            )


def collect_chapters(nodes):
    chapters = []
    current_nodes = []
    current_ch_num = None

    for node in nodes:
        chapter_number = parse_chapter_header_number(node)
        if chapter_number is not None:
            if current_ch_num is not None:
                chapters.append((current_ch_num, current_nodes))
                current_nodes = []

            current_ch_num = chapter_number
            current_nodes.append(node)
            continue

        if current_ch_num is not None:
            current_nodes.append(node)

    if current_ch_num is not None and current_nodes:
        chapters.append((current_ch_num, current_nodes))

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
            lessons.append((current_ch, current_sec, current_sec_title, current_nodes))
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
            current_sec_title = title_rest if title_rest else f"Sezione {current_ch}.{current_sec}"
            expected_sec = sec_no + 1
            continue

        if current_ch is not None and current_sec is not None:
            current_nodes.append(node)

    flush_current()

    return lessons, warnings


def write_chapter_outputs(chapters, out_dir, out_format, source):
    count = 0

    for chapter_number, chapter_nodes in chapters:
        nodes_copy = [deepcopy(node) for node in chapter_nodes]
        name_num = f"{chapter_number:02d}" if isinstance(chapter_number, int) else "xx"
        title_text = f"Capitolo {chapter_number}" if isinstance(chapter_number, int) else "Capitolo"

        if out_format == "html":
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.html")
            write_html(out_path, title_text, nodes_copy, source)
        elif out_format == "txt":
            parts = []
            for node in nodes_copy:
                text = itertext(node).strip()
                if text:
                    parts.append(text)
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write("\n\n".join(parts))
        else:
            out_path = os.path.join(out_dir, f"Capitolo-{name_num}.epub")
            write_epub(out_path, title_text, nodes_copy, source)

        count += 1
        print(f"Wrote {out_path}")

    print(f"Done. Wrote {count} files to {out_dir}")


def write_section_outputs(lessons, out_dir, out_format, source):
    count = 0

    for ch_num, sec_num, sec_title, sec_nodes in lessons:
        nodes_copy = [deepcopy(node) for node in sec_nodes]
        chapter_header = ET.Element(f"{{{NS['x']}}}h1")
        chapter_header.text = f"Capitolo {ch_num}"
        section_header = ET.Element(f"{{{NS['x']}}}h2")
        section_header.text = f"{ch_num}.{sec_num} {sec_title}".strip()
        content_nodes = [chapter_header, section_header] + nodes_copy

        name_ch = f"{ch_num:02d}" if isinstance(ch_num, int) else "xx"
        name_sec = f"{sec_num:02d}" if isinstance(sec_num, int) else "yy"
        title_text = f"Capitolo {ch_num} - {ch_num}.{sec_num} {sec_title}".strip()

        if out_format == "html":
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.html")
            write_html(out_path, title_text, content_nodes, source)
        elif out_format == "txt":
            parts = [f"Capitolo {ch_num}", f"{ch_num}.{sec_num} {sec_title}".strip()]
            for node in nodes_copy:
                text = itertext(node).strip()
                if text:
                    parts.append(text)
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.txt")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write("\n\n".join(parts))
        else:
            out_path = os.path.join(out_dir, f"Capitolo-{name_ch}-{name_sec}.epub")
            write_epub(out_path, title_text, content_nodes, source)

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
                    "No chapters found. Looked for <h2> with text starting 'Capitolo '",
                    file=sys.stderr,
                )
                sys.exit(4)
            write_chapter_outputs(chapters, out_dir, args.format, source)
            return

        lessons, warnings = collect_lessons(nodes)
        if not lessons:
            print(
                "No sections found. Looked for <h3> with text like '1.1 Title'",
                file=sys.stderr,
            )
            sys.exit(5)

        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        write_section_outputs(lessons, out_dir, args.format, source)
    finally:
        source.close()


if __name__ == "__main__":
    main()
