from dataclasses import dataclass, field
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Chapter:
    number: int
    nodes: list[ET.Element]


@dataclass(frozen=True)
class Lesson:
    chapter_number: int
    section_number: int
    title: str
    nodes: list[ET.Element]


@dataclass
class RenderState:
    title: str
    nodes: list[ET.Element]
    source: object
    image_prefix: str
    strip_english_annotations: bool = True
    assets: dict[str, bytes] = field(default_factory=dict)
