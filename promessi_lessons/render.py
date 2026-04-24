import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET
import zipfile

from promessi_lessons.model import RenderState
from promessi_lessons.transforms import (
    CollectAssetsTransform,
    NormalizeLinksTransform,
    StripAudioLinksTransform,
    StripEnglishAnnotationsTransform,
    StripPageBreaksTransform,
    TransformPipeline,
)
from promessi_lessons.xml import EPUB_NS, NS, XML_NS, deepcopy, itertext, media_type_for_path


def make_doc_minimal(title_text, nodes):
    html = ET.Element(
        f"{{{NS['x']}}}html",
        attrib={f"{{{XML_NS}}}lang": "it", "lang": "it"},
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


def build_render_state(
    title_text,
    content_nodes,
    source,
    image_prefix,
    *,
    strip_english_annotations=True,
):
    nodes = [deepcopy(node) for node in content_nodes]
    state = RenderState(
        title=title_text,
        nodes=nodes,
        source=source,
        image_prefix=image_prefix,
        strip_english_annotations=strip_english_annotations,
    )
    pipeline = TransformPipeline(
        [
            StripPageBreaksTransform(),
            StripAudioLinksTransform(),
            StripEnglishAnnotationsTransform(),
            NormalizeLinksTransform(),
            CollectAssetsTransform(),
        ]
    )
    return pipeline.apply(state)


def write_html(
    out_path,
    title_text,
    content_nodes,
    source,
    *,
    strip_english_annotations=True,
):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    state = build_render_state(
        title_text,
        content_nodes,
        source,
        image_prefix="images",
        strip_english_annotations=strip_english_annotations,
    )
    doc = make_doc_minimal(title_text, state.nodes)
    ET.ElementTree(doc).write(out_path, encoding="utf-8", xml_declaration=True, method="xml")

    if state.assets:
        images_dir = Path(out_path).parent / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        for asset_name, data in state.assets.items():
            (images_dir / asset_name).write_bytes(data)


def write_epub(
    out_path,
    title_text,
    content_nodes,
    source,
    *,
    strip_english_annotations=True,
):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    state = build_render_state(
        title_text,
        content_nodes,
        source,
        image_prefix="../images",
        strip_english_annotations=strip_english_annotations,
    )
    content_doc = serialize_xml(make_epub_content_doc(title_text, state.nodes))
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

    for index, asset_name in enumerate(sorted(state.assets), start=1):
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
        for asset_name, data in sorted(state.assets.items()):
            zf.writestr(
                f"OEBPS/images/{asset_name}",
                data,
                compress_type=zipfile.ZIP_DEFLATED,
            )


def flatten_text(nodes):
    parts = []
    for node in nodes:
        text = itertext(node).strip()
        if text:
            parts.append(text)
    return parts


def write_text(out_path, sections):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(sections))
