"""HTML file parser with tag counting and text extraction."""

from html.parser import HTMLParser
from typing import TypedDict
from ._meta import FileMeta, file_meta


class _TagCounter(HTMLParser):
    """Count HTML tags and extract text content.

    Skips script and style elements when extracting text.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tags: dict[str, int] = {}
        self.text_parts: list[str] = []
        self._in_script = False
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag == "script":
            self._in_script = True
        elif tag == "style":
            self._in_style = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_script = False
        elif tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if not self._in_script and not self._in_style:
            text = data.strip()
            if text:
                self.text_parts.append(text)


class HtmlResult(FileMeta):
    """Parsed HTML file metadata.

    Attributes:
        type: Always "html".
        content: Raw HTML content.
        tags: Tag name to count mapping.
        text_length: Total text character count.
        title: Page title from <title> tag.
    """
    type: str
    content: str
    tags: dict[str, int]
    text_length: int
    title: str


def parse_html(path: str) -> HtmlResult:
    """Parse an HTML file.

    Extracts text content, tag statistics, and page title.

    Args:
        path: str — path to the HTML file.

    Returns:
        dict: {
            "type": str — always "html",
            "content": str — extracted text content,
            "tags": dict[str, int] — tag name to count mapping,
            "text_length": int — total text character count,
            "title": str — page title from <title> tag,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    counter = _TagCounter()
    try:
        counter.feed(raw)
    except Exception:
        pass

    title = ""
    try:
        start = raw.lower().find("<title>")
        end = raw.lower().find("</title>", start)
        if start != -1 and end != -1:
            title = raw[start + 7:end].strip()
    except Exception:
        pass

    text = "\n".join(counter.text_parts)

    lines = [f"Title: {title or '(none)'}"]
    lines.append(f"Text length: {len(text)} chars")
    lines.append(f"Unique tags: {len(counter.tags)}")
    lines.append("")
    for tag, count in sorted(counter.tags.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"  <{tag}>: {count}")
    lines.append("")
    lines.append("--- Text content ---")
    lines.append(text[:5000])
    if len(text) > 5000:
        lines.append(f"\n... ({len(text) - 5000} more chars)")

    return {
        "type": "html",
        "content": raw,
        "tags": counter.tags,
        "text_length": len(text),
        "title": title,
        "text_preview": "\n".join(lines),
        **file_meta(path),
    }
