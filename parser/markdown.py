import markdown
from .text import TextResult


def parse_md(path: str) -> TextResult:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    html = markdown.markdown(text, extensions=["fenced_code", "tables", "nl2br"])
    return {
        "type": "markdown",
        "content": html,
        "lines": len(text.splitlines()),
    }
