import configparser
from typing import TypedDict
from ._meta import FileMeta, file_meta


class ConfigResult(FileMeta):
    """Parsed config file metadata."""
    type: str
    content: str
    sections: list[str]
    keys: list[str]


def parse_ini(path: str) -> ConfigResult:
    """Parse an INI/CFG/CONF file using configparser.

    Args:
        path: str — path to the config file.

    Returns:
        dict: {
            "type": str — always "ini",
            "content": str — formatted config content,
            "sections": list[str] — section names,
            "keys": list[str] — all key=value pairs as "section.key" strings,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    parser = configparser.ConfigParser()
    parser.optionxform = str  # preserve key case

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    parser.read_string(content)

    sections = list(parser.sections())
    all_keys: list[str] = []
    lines: list[str] = []

    if parser.defaults():
        lines.append("[DEFAULT]")
        for k, v in parser.defaults().items():
            lines.append(f"  {k} = {v}")
            all_keys.append(f"DEFAULT.{k}")

    for section in sections:
        lines.append(f"\n[{section}]")
        for k, v in parser[section].items():
            lines.append(f"  {k} = {v}")
            all_keys.append(f"{section}.{k}")

    return {
        "type": "ini",
        "content": "\n".join(lines),
        "sections": sections,
        "keys": all_keys,
        **file_meta(path),
    }


def parse_properties(path: str) -> ConfigResult:
    """Parse a Java-style .properties file.

    Args:
        path: str — path to the .properties file.

    Returns:
        dict: {
            "type": str — always "properties",
            "content": str — formatted key=value pairs,
            "sections": list[str] — empty (no sections in properties),
            "keys": list[str] — all property keys,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    props: dict[str, str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
            elif ":" in line:
                k, v = line.split(":", 1)
                props[k.strip()] = v.strip()

    lines = [f"{k} = {v}" for k, v in props.items()]

    return {
        "type": "properties",
        "content": "\n".join(lines),
        "sections": [],
        "keys": list(props.keys()),
        **file_meta(path),
    }
