from typing import TypedDict
from ._meta import FileMeta, file_meta


class TomlResult(FileMeta):
    """Parsed TOML file metadata."""
    type: str
    content: str
    keys: list[str] | None
    items: int | None


def parse_toml(path: str) -> TomlResult:
    """Parse a TOML file using tomllib (stdlib 3.11+).

    Args:
        path: str — path to the TOML file.

    Returns:
        dict: {
            "type": str — always "toml",
            "content": str — formatted TOML string,
            "keys": list[str] — top-level keys,
            "items": int — number of top-level items,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    import tomllib

    with open(path, "rb") as f:
        data = tomllib.load(f)

    lines: list[str] = []
    _dump_toml(data, lines, prefix="")
    formatted = "\n".join(lines)

    keys = list(data.keys()) if isinstance(data, dict) else None
    items = len(data) if isinstance(data, (dict, list)) else None

    return {
        "type": "toml",
        "content": formatted,
        "keys": keys,
        "items": items,
        **file_meta(path),
    }


def _dump_toml(data: dict | list | str | int | float | bool | None, lines: list[str], prefix: str) -> None:
    """Recursively format TOML data into readable lines."""
    if isinstance(data, dict):
        simple = {}
        for k, v in data.items():
            if isinstance(v, dict):
                section = f"{prefix}.{k}" if prefix else k
                lines.append(f"\n[{section}]")
                _dump_toml(v, lines, section)
            else:
                simple[k] = v
        for k, v in simple.items():
            lines.append(f"{k} = {_toml_value(v)}")
    elif isinstance(data, list):
        items = [_toml_value(item) for item in data]
        lines.append(f"[{', '.join(items)}]")
    else:
        lines.append(f"= {_toml_value(data)}")


def _toml_value(v: object) -> str:
    """Format a single TOML value."""
    if isinstance(v, str):
        return f'"{v}"'
    elif isinstance(v, bool):
        return "true" if v else "false"
    elif isinstance(v, (int, float)):
        return str(v)
    elif v is None:
        return '""'
    return str(v)
