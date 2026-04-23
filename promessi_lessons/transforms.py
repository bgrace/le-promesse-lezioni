import os
from pathlib import PurePosixPath
import re

from promessi_lessons.model import RenderState
from promessi_lessons.xml import is_local_reference, unwrap_google_redirect

ENGLISH_GLOSS_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 .,';:!?/-]*$")


class TransformPipeline:
    def __init__(self, transforms):
        self.transforms = list(transforms)

    def apply(self, state: RenderState):
        for transform in self.transforms:
            transform.apply(state)
        return state


class StripPageBreaksTransform:
    def apply(self, state: RenderState):
        parent_map = {}
        for node in state.nodes:
            for parent in node.iter():
                for child in parent:
                    parent_map[child] = parent
        for node in state.nodes:
            for child in list(child_walk(node)):
                if child.tag != "{http://www.w3.org/1999/xhtml}hr":
                    continue
                parent = parent_map.get(child)
                if parent is not None:
                    parent.remove(child)


class NormalizeLinksTransform:
    def apply(self, state: RenderState):
        ids_in_document = {
            child.attrib["id"]
            for node in state.nodes
            for child in node.iter()
            if child.attrib.get("id")
        }

        for node in state.nodes:
            for child in node.iter():
                if child.tag != "{http://www.w3.org/1999/xhtml}a":
                    continue
                href = child.attrib.get("href")
                if not href:
                    continue
                rewritten = unwrap_google_redirect(href)
                if rewritten.startswith("#") and rewritten[1:] not in ids_in_document:
                    child.attrib.pop("href", None)
                    continue
                child.set("href", rewritten)


class StripEnglishAnnotationsTransform:
    def apply(self, state: RenderState):
        if not state.strip_english_annotations:
            return

        for node in state.nodes:
            for parent in [node, *list(node.iter())]:
                self._strip_from_parent(parent)

    def _strip_from_parent(self, parent):
        children = list(parent)
        index = 0
        while index < len(children):
            child = children[index]
            if not self._looks_like_gloss_node(child):
                index += 1
                continue

            if not self._strip_gloss_triplet(parent, children, index):
                index += 1
                continue

            children = list(parent)

    def _strip_gloss_triplet(self, parent, children, index):
        previous = children[index - 1] if index > 0 else None
        next_child = children[index + 1] if index + 1 < len(children) else None
        if previous is None or next_child is None:
            return False

        previous_node, previous_attr = self._trailing_text_slot(previous)
        next_node, next_attr = self._leading_text_slot(next_child)
        previous_text = getattr(previous_node, previous_attr)
        next_text = getattr(next_node, next_attr)

        if previous_text is None or next_text is None:
            return False
        if not previous_text.rstrip().endswith("(="):
            return False
        if not next_text.lstrip().startswith(")"):
            return False

        setattr(previous_node, previous_attr, self._trim_annotation_open(previous_text))
        setattr(next_node, next_attr, self._trim_annotation_close(next_text))
        parent.remove(children[index])
        return True

    def _looks_like_gloss_node(self, node):
        text = "".join(node.itertext()).strip()
        return bool(text) and ENGLISH_GLOSS_RE.fullmatch(text) is not None

    def _trim_annotation_open(self, text):
        stripped = text.rstrip()
        stripped = stripped[:-2].rstrip()
        suffix = text[len(text.rstrip()):]
        return stripped + suffix

    def _trim_annotation_close(self, text):
        stripped = text.lstrip()
        if stripped.startswith(")"):
            stripped = stripped[1:].lstrip()
        prefix = text[: len(text) - len(text.lstrip())]
        return prefix + stripped

    def _trailing_text_slot(self, node):
        if len(node):
            return node[-1], "tail"
        return node, "text"

    def _leading_text_slot(self, node):
        if node.text is not None:
            return node, "text"
        if len(node):
            return self._leading_text_slot(node[0])
        return node, "text"


class CollectAssetsTransform:
    def apply(self, state: RenderState):
        asset_names = {}

        for node in state.nodes:
            for child in node.iter():
                if child.tag != "{http://www.w3.org/1999/xhtml}img":
                    continue

                src = child.attrib.get("src")
                if not is_local_reference(src):
                    continue

                try:
                    asset_name = self._ensure_asset_name(state, asset_names, src)
                except (FileNotFoundError, KeyError):
                    continue

                child.set("src", f"{state.image_prefix}/{asset_name}")
                if not child.attrib.get("alt"):
                    child.set("alt", os.path.splitext(asset_name)[0])

    def _ensure_asset_name(self, state, asset_names, reference):
        resolved = state.source.resolve_local_ref(reference)
        existing = asset_names.get(resolved)
        if existing:
            return existing

        base = PurePosixPath(reference).name or PurePosixPath(resolved).name
        stem, ext = os.path.splitext(base)
        candidate = base
        index = 2
        while candidate in state.assets:
            candidate = f"{stem}-{index}{ext}"
            index += 1

        state.assets[candidate] = state.source.read_local_ref(reference)
        asset_names[resolved] = candidate
        return candidate


def child_walk(node):
    yield node
    for child in node:
        yield from child_walk(child)
