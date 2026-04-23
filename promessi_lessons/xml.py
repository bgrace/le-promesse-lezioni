import os
import re
import urllib.parse
import xml.etree.ElementTree as ET


NS = {"x": "http://www.w3.org/1999/xhtml"}
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}
XML_NS = "http://www.w3.org/XML/1998/namespace"
EPUB_NS = "http://www.idpf.org/2007/ops"
SEC_RE = re.compile(r"^(\d+)\.(\d+)\b(.*)")
CHAPTER_RE = re.compile(r"^Capitolo\s+(\d+)\b")
HEADING_TAGS = {f"{{{NS['x']}}}h1", f"{{{NS['x']}}}h2", f"{{{NS['x']}}}h3"}


def itertext(elem):
    return "".join(elem.itertext()) if elem is not None else ""


def deepcopy(elem):
    new = ET.Element(elem.tag, attrib=dict(elem.attrib))
    new.text = elem.text
    new.tail = elem.tail
    for child in list(elem):
        new.append(deepcopy(child))
    return new


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

