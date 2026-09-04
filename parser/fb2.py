"""FB2 (FictionBook 2.x) ebook parser with chapter extraction and image support."""

import base64
import os
import re
import tempfile
import shutil
from xml.etree import ElementTree as ET
from typing import TypedDict
from ._meta import FileMeta, file_meta

FB2_NS = "http://www.gribuser.ru/xml/fictionbook/2.0"


class Fb2Result(FileMeta):
    """Parsed FB2 file metadata.

    Attributes:
        type: Always "fb2".
        content: HTML content of the first chapter.
        title: Book title.
        creator: Author name.
        language: Language code.
        chapters: List of chapter dicts with html and title.
        chapter_count: Total number of chapters.
        current_index: Current chapter index (0).
        images_dir: Path to extracted images directory.
    """
    type: str
    content: str
    title: str
    creator: str
    language: str
    chapters: list[dict]
    chapter_count: int
    current_index: int
    images_dir: str


def _tag(name: str) -> str:
    """Build a namespaced tag name."""
    return f"{{{FB2_NS}}}{name}"


def _text(el, default: str = "") -> str:
    """Extract text content from an element."""
    if el is None:
        return default
    return (el.text or "").strip()


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _extract_binary_images(root, tmp_dir: str) -> dict[str, str]:
    """Extract base64-encoded <binary> images to a temp directory.

    Args:
        root: FB2 XML root element.
        tmp_dir: Temp directory to write images to.

    Returns:
        Dict mapping binary id to absolute file path.
    """
    images = {}
    for binary in root.findall(_tag("binary")):
        binary_id = binary.get("id", "")
        content_type = binary.get("content-type", "image/png")
        if not binary_id or not binary.text:
            continue

        ext = content_type.split("/")[-1].split(";")[0]
        if ext == "jpeg":
            ext = "jpg"

        try:
            data = base64.b64decode(binary.text.strip())
        except Exception:
            continue

        filename = f"{binary_id}.{ext}"
        filepath = os.path.join(tmp_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(data)
            images[binary_id] = filepath
        except Exception:
            continue

    return images


def _element_to_html(el, images: dict[str, str]) -> str:
    """Convert an FB2 XML element to HTML recursively.

    Args:
        el: XML element to convert.
        images: Dict mapping binary id to file path.

    Returns:
        HTML string.
    """
    if el is None:
        return ""

    tag = el.tag
    if tag and tag.startswith(f"{{{FB2_NS}}}"):
        tag = tag[len(f"{{{FB2_NS}}}"):]

    parts = []
    if el.text:
        parts.append(_escape(el.text))
    for child in el:
        parts.append(_element_to_html(child, images))
        if child.tail:
            parts.append(_escape(child.tail))
    children_html = "".join(parts)

    if tag == "section":
        return f'<div class="section">{children_html}</div>'
    elif tag == "title":
        return f'<div class="chapter-title">{children_html}</div>'
    elif tag == "p":
        return f"<p>{children_html}</p>"
    elif tag == "subtitle":
        return f'<p class="subtitle">{children_html}</p>'
    elif tag == "epigraph":
        return f'<blockquote class="epigraph">{children_html}</blockquote>'
    elif tag == "cite":
        return f'<blockquote class="cite">{children_html}</blockquote>'
    elif tag == "poem":
        return f'<div class="poem">{children_html}</div>'
    elif tag == "stanza":
        return f'<div class="stanza">{children_html}</div>'
    elif tag == "v":
        return f"<p>{children_html}</p>"
    elif tag in ("emphasis", "em"):
        return f"<em>{children_html}</em>"
    elif tag == "strong":
        return f"<strong>{children_html}</strong>"
    elif tag == "strikethrough":
        return f"<s>{children_html}</s>"
    elif tag == "code":
        return f"<code>{children_html}</code>"
    elif tag == "empty-line":
        return "<br/>"
    elif tag == "image":
        href = el.get("l:href", "") or el.get("{http://www.w3.org/1999/xlink}href", "")
        if href.startswith("#"):
            href = href[1:]
        img_path = images.get(href, "")
        if img_path:
            safe_path = img_path.replace("\\", "/")
            return f'<img src="{safe_path}"/>'
        return ""
    elif tag == "a":
        href = el.get("l:href", "") or el.get("{http://www.w3.org/1999/xlink}href", "")
        return f'<a href="{href}">{children_html}</a>'
    elif tag == "text-author":
        return f'<p class="text-author">{children_html}</p>'
    elif tag == "date":
        return f'<span class="date">{children_html}</span>'
    elif tag == "genre":
        return ""
    elif tag == "first-name":
        return ""
    elif tag == "middle-name":
        return ""
    elif tag == "last-name":
        return ""
    elif tag == "description":
        return ""
    elif tag == "binary":
        return ""
    elif tag == "stylesheet":
        return ""
    else:
        return children_html


def _extract_description(root) -> dict:
    """Extract metadata from <description> element.

    Args:
        root: FB2 XML root element.

    Returns:
        Dict with title, creator, language.
    """
    desc = root.find(_tag("description"))
    if desc is None:
        return {"title": "", "creator": "", "language": ""}

    title_info = desc.find(_tag("title-info"))
    title = ""
    creator = ""
    language = ""

    if title_info is not None:
        book_title = title_info.find(_tag("book-title"))
        title = _text(book_title)

        author = title_info.find(_tag("author"))
        if author is not None:
            first = _text(author.find(_tag("first-name")))
            last = _text(author.find(_tag("last-name")))
            middle = _text(author.find(_tag("middle-name")))
            parts = [p for p in [first, middle, last] if p]
            creator = " ".join(parts)

        lang = title_info.find(_tag("lang"))
        language = _text(lang)

    return {"title": title, "creator": creator, "language": language}


def parse_fb2(path: str) -> Fb2Result:
    """Parse an FB2 ebook file.

    Extracts chapters as HTML with metadata and embedded images.

    Args:
        path: Path to the FB2 file.

    Returns:
        Fb2Result dict with chapters, metadata, and images_dir.
    """
    error_result = {
        "type": "fb2", "content": "",
        "title": "", "creator": "", "language": "",
        "chapters": [], "chapter_count": 0, "current_index": 0,
        "images_dir": "", **file_meta(path),
    }

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            xml_content = f.read()
    except OSError as e:
        return {**error_result, "content": f"[Error reading FB2 file]: {e}"}

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return {**error_result, "content": f"[Error parsing FB2 XML]: {e}"}

    meta = _extract_description(root)

    tmp_dir = tempfile.mkdtemp(prefix="fb2_img_")
    images = _extract_binary_images(root, tmp_dir)
    if not images:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        tmp_dir = ""

    chapters = []
    bodies = root.findall(_tag("body"))
    for body in bodies:
        sections = body.findall(_tag("section"))
        for section in sections:
            title_el = section.find(_tag("title"))
            ch_title = ""
            if title_el is not None:
                title_text_parts = []
                for p in title_el.findall(_tag("p")):
                    t = _text(p)
                    if t:
                        title_text_parts.append(t)
                ch_title = " ".join(title_text_parts)

            section_html = _element_to_html(section, images)

            if not ch_title:
                plain = re.sub(r"<[^>]+>", "", section_html).strip()
                ch_title = plain[:50] + "..." if len(plain) > 50 else plain or "Без названия"

            chapters.append({
                "html": section_html,
                "title": ch_title,
            })

    content = chapters[0]["html"] if chapters else ""

    return {
        "type": "fb2",
        "content": content,
        "title": meta["title"],
        "creator": meta["creator"],
        "language": meta["language"],
        "chapters": chapters,
        "chapter_count": len(chapters),
        "current_index": 0,
        "images_dir": tmp_dir,
        **file_meta(path),
    }
