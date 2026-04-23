import os
from pathlib import PurePosixPath

from promessi_lessons.model import RenderState
from promessi_lessons.xml import is_local_reference, unwrap_google_redirect


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
