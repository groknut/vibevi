from typing import TypedDict
from ._meta import FileMeta, file_meta


class TextResult(FileMeta):
    type: str
    content: str
    lines: int


def parse_txt(path: str) -> TextResult:
    """Parse a plain text file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return {
        "type": "text",
        "content": text,
        "lines": len(text.splitlines()),
        **file_meta(path),
    }


def _make_text_parser(type_name: str):
    """Factory for text-based parsers that differ only by type name."""
    def parser(path: str) -> TextResult:
        result = parse_txt(path)
        result["type"] = type_name
        return result
    return parser


parse_md = _make_text_parser("markdown")
parse_log = _make_text_parser("log")
