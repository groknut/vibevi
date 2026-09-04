"""JSON and XML file parsers."""

import json
import xml.etree.ElementTree as ET
from typing import Any, TypedDict
from ._meta import FileMeta, file_meta


class JsonResult(FileMeta):
    """Parsed JSON file metadata.

    Attributes:
        type: Always "json".
        content: Pretty-printed JSON string.
        content_type: Python type name of the root value.
        keys: Top-level keys if root is a dict, else None.
        items: Number of items if root is dict or list, else None.
        value: Scalar value if root is neither dict nor list.
    """
    type: str
    content: str
    content_type: str
    keys: list[str] | None
    items: int | None
    value: Any | None


class XmlResult(FileMeta):
    """Parsed XML file metadata.

    Attributes:
        type: Always "xml".
        content: Indented XML string representation.
        root_tag: Tag name of the root element.
        elements: Total element count.
        attributes: Attributes of the root element.
    """
    type: str
    content: str
    root_tag: str
    elements: int
    attributes: dict[str, str]


def parse_json(path: str) -> JsonResult:
    """Parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        JsonResult with formatted content and structural info.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    formatted = json.dumps(data, indent=2, ensure_ascii=False)
    content_type = type(data).__name__

    result: JsonResult = {
        "type": "json",
        "content": formatted,
        "content_type": content_type,
        "keys": None,
        "items": None,
        "value": None,
        **file_meta(path),
    }

    if isinstance(data, dict):
        result["keys"] = list(data.keys())
        result["items"] = len(data)
    elif isinstance(data, list):
        result["items"] = len(data)
    else:
        result["value"] = data

    return result


def _dump_element(element: ET.Element, lines: list[str], indent: int) -> None:
    """Recursively serialize an XML element tree into indented string lines.

    Args:
        element: The XML element to serialize.
        lines: Accumulator list for output lines.
        indent: Current indentation level.
    """
    prefix = "  " * indent
    attrs = " ".join(f'{k}="{v}"' for k, v in element.attrib.items())
    tag = element.tag
    text = (element.text or "").strip()

    if attrs:
        tag = f"{tag} {attrs}"

    if len(element) == 0 and text:
        lines.append(f"{prefix}<{tag}> {text} </{element.tag}>")
    elif len(element) == 0:
        lines.append(f"{prefix}<{tag} />")
    else:
        lines.append(f"{prefix}<{tag}>")
        if text:
            lines.append(f"{prefix}  {text}")
        for child in element:
            _dump_element(child, lines, indent + 1)
        lines.append(f"{prefix}</{element.tag}>")


def parse_xml(path: str) -> XmlResult:
    """Parse an XML file.

    Args:
        path: Path to the XML file.

    Returns:
        XmlResult with formatted content and element stats.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    lines: list[str] = []
    _dump_element(root, lines, indent=0)

    element_count = sum(1 for _ in root.iter())
    return {
        "type": "xml",
        "content": "\n".join(lines),
        "root_tag": root.tag,
        "elements": element_count,
        "attributes": dict(root.attrib),
        **file_meta(path),
    }
