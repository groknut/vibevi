"""Plain text and log file parser."""

from typing import TypedDict
from ._meta import FileMeta, file_meta


class TextResult(FileMeta):
    """Parsed text file metadata.

    Attributes:
        type: Always "text" (or variant like "log", "markdown").
        content: Full text content.
        lines: Number of lines.
    """
    type: str
    content: str
    lines: int


def parse_txt(path: str) -> TextResult:
    """Parse a plain text file.

    Args:
        path: Path to the text file.

    Returns:
        TextResult with content and line count.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return {
        "type": "text",
        "content": text,
        "lines": len(text.splitlines()),
        **file_meta(path),
    }


def _make_text_parser(type_name: str):
    """Factory for text-based parsers that differ only by type name.

    Args:
        type_name: The type string to set in the result dict.

    Returns:
        A parser function that reads a file and sets the given type.
    """
    def parser(path: str) -> TextResult:
        result = parse_txt(path)
        result["type"] = type_name
        return result
    return parser


parse_md = _make_text_parser("markdown")
parse_log = _make_text_parser("log")
