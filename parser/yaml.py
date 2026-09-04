"""YAML file parser using PyYAML."""

from typing import TypedDict
from ._meta import FileMeta, file_meta


class YamlResult(FileMeta):
    """Parsed YAML file metadata.

    Attributes:
        type: Always "yaml".
        content: Pretty-printed YAML string.
        keys: Top-level keys if root is a mapping.
        items: Number of items if root is mapping or sequence.
    """
    type: str
    content: str
    keys: list[str] | None
    items: int | None


def parse_yaml(path: str) -> YamlResult:
    """Parse a YAML file using PyYAML.

    Args:
        path: str — path to the YAML file.

    Returns:
        dict: {
            "type": str — always "yaml",
            "content": str — pretty-printed YAML string,
            "keys": list[str] — top-level keys (if mapping),
            "items": int — number of items (if mapping or sequence),
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        import yaml
    except ImportError:
        return {"type": "yaml", "content": "[PyYAML not installed]", "keys": None, "items": None, **file_meta(path)}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    formatted = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    keys = None
    items = None
    if isinstance(data, dict):
        keys = list(data.keys())
        items = len(data)
    elif isinstance(data, list):
        items = len(data)

    return {
        "type": "yaml",
        "content": formatted,
        "keys": keys,
        "items": items,
        **file_meta(path),
    }
