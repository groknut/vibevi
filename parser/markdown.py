"""Markdown file parser with optional HTML conversion."""

from .text import TextResult, parse_txt


def parse_md(path: str) -> TextResult:
    """Parse a Markdown file, converting to HTML if markdown library is available.

    Falls back to plain text if the `markdown` package is not installed.

    Args:
        path: Path to the Markdown file.

    Returns:
        TextResult with HTML content (or raw text).
    """
    try:
        import markdown
    except ImportError:
        result = parse_txt(path)
        result["type"] = "markdown"
        return result

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    html = markdown.markdown(text, extensions=["fenced_code", "tables", "nl2br"])
    return {
        "type": "markdown",
        "content": html,
        "lines": len(text.splitlines()),
    }
