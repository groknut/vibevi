import xml.etree.ElementTree as ET
from typing import TypedDict
from ._meta import FileMeta, file_meta


class SvgResult(FileMeta):
    """Parsed SVG file metadata."""
    type: str
    content: str
    width: str
    height: str
    viewbox: str
    elements: int


def parse_svg(path: str) -> SvgResult:
    """Parse an SVG file.

    Extracts dimensions, viewbox, and element count.

    Args:
        path: str — path to the SVG file.

    Returns:
        dict: {
            "type": str — always "svg",
            "content": str — SVG structure summary,
            "width": str — width attribute,
            "height": str — height attribute,
            "viewbox": str — viewBox attribute,
            "elements": int — total number of SVG elements,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    tree = ET.parse(path)
    root = tree.getroot()

    ns = {"svg": "http://www.w3.org/2000/svg"}
    width = root.get("width", "")
    height = root.get("height", "")
    viewbox = root.get("viewBox", "")

    if not width:
        w = root.attrib.get("{http://www.w3.org/2000/svg}width", "")
        if not w:
            w = root.get("width", "")
        width = w
    if not height:
        h = root.attrib.get("{http://www.w3.org/2000/svg}height", "")
        if not h:
            h = root.get("height", "")
        height = h
    if not viewbox:
        vb = root.attrib.get("{http://www.w3.org/2000/svg}viewBox", "")
        if not vb:
            vb = root.get("viewBox", "")
        viewbox = vb

    element_count = sum(1 for _ in root.iter())

    tag_counts: dict[str, int] = {}
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        tag_counts[local] = tag_counts.get(local, 0) + 1

    lines = [
        f"Size: {width} x {height}",
        f"ViewBox: {viewbox or '(none)'}",
        f"Total elements: {element_count}",
        "",
        "Element breakdown:",
    ]
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:15]:
        lines.append(f"  <{tag}>: {count}")

    return {
        "type": "svg",
        "content": "\n".join(lines),
        "width": width,
        "height": height,
        "viewbox": viewbox,
        "elements": element_count,
        **file_meta(path),
    }
