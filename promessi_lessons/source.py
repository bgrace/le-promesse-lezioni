import posixpath
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from promessi_lessons.xml import CONTAINER_NS, OPF_NS


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

