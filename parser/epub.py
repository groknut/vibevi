"""EPUB ebook parser with chapter extraction and image support."""

import zipfile
import re
import os
import tempfile
import shutil
from xml.etree import ElementTree as ET
from typing import TypedDict
from ._meta import FileMeta, file_meta

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp")
"""Supported image file extensions for EPUB image extraction."""


class EpubResult(FileMeta):
    """Parsed EPUB file metadata.

    Attributes:
        type: Always "epub".
        content: HTML content of the first chapter.
        title: Book title.
        creator: Author name.
        language: Language code.
        chapters: List of chapter dicts with href, html, title.
        chapter_count: Total number of chapters.
        current_index: Current chapter index (0).
        files: All file paths in the archive.
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
    files: list[str]
    images_dir: str


def _parse_opf(zf: zipfile.ZipFile, opf_path: str) -> dict:
    """Parse content.opf to extract metadata and spine order.

    Args:
        zf: Opened ZipFile object.
        path: Path to the .opf file inside the archive.

    Returns:
        Dict with title, creator, language, and spine list.
    """
    with zf.open(opf_path) as f:
        opf_xml = f.read().decode("utf-8", errors="replace")

    ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
    try:
        root = ET.fromstring(opf_xml)
    except ET.ParseError:
        return {"title": "", "creator": "", "language": "", "spine": []}

    manifest = {}
    for item in root.findall(".//opf:manifest/opf:item", ns):
        item_id = item.get("id", "")
        href = item.get("href", "")
        manifest[item_id] = href

    spine = []
    for itemref in root.findall(".//opf:spine/opf:itemref", ns):
        idref = itemref.get("idref", "")
        if idref in manifest:
            spine.append(manifest[idref])

    metadata = root.find(".//opf:metadata", ns)
    title = ""
    creator = ""
    language = ""
    if metadata is not None:
        t = metadata.find("dc:title", ns)
        if t is not None and t.text:
            title = t.text.strip()
        c = metadata.find("dc:creator", ns)
        if c is not None and c.text:
            creator = c.text.strip()
        l = metadata.find("dc:language", ns)
        if l is not None and l.text:
            language = l.text.strip()

    return {"title": title, "creator": creator, "language": language, "spine": spine}


def _extract_images(zf: zipfile.ZipFile, names: list[str], opf_dir: str) -> str:
    """Extract images from EPUB to a temp directory.

    Args:
        zf: Opened ZipFile object.
        names: List of file paths in the archive.
        opf_dir: Directory of the OPF file for path resolution.

    Returns:
        Path to the temp directory containing extracted images, or "".
    """
    img_names = [n for n in names if n.lower().endswith(IMAGE_EXTS)]
    if not img_names:
        return ""

    tmp_dir = tempfile.mkdtemp(prefix="epub_img_")
    for img in img_names:
        try:
            data = zf.read(img)
            out_path = os.path.join(tmp_dir, img.replace("/", os.sep))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
        except Exception:
            continue
    return tmp_dir


def _rewrite_image_paths(html: str, images_dir: str, opf_dir: str) -> str:
    """Replace relative image paths with absolute paths.

    Handles src and xlink:href attributes in HTML.

    Args:
        html: Raw HTML content.
        images_dir: Path to extracted images directory.
        opf_dir: OPF-relative directory prefix.

    Returns:
        HTML with rewritten image paths.
    """
    if not images_dir:
        return html

    def _replace(match: re.Match) -> str:
        prefix = match.group(1)
        rel_path = match.group(2)
        suffix = match.group(3)

        full_rel = opf_dir + rel_path if opf_dir else rel_path
        abs_path = os.path.join(images_dir, full_rel.replace("/", os.sep))
        if os.path.isfile(abs_path):
            abs_url = abs_path.replace("\\", "/")
            return f'{prefix}{abs_url}{suffix}'
        return match.group(0)

    html = re.sub(r'(src=")([^"]+)(")', _replace, html)
    html = re.sub(r"(src=')([^']+)(')", _replace, html)
    html = re.sub(r'(xlink:href=")([^"]+)(")', _replace, html)
    html = re.sub(r"(xlink:href=')([^']+)(')", _replace, html)
    return html


def cleanup_epub_images(images_dir: str):
    """Remove temp images directory.

    Args:
        images_dir: Path to the temp directory to remove.
    """
    if images_dir and os.path.isdir(images_dir):
        try:
            shutil.rmtree(images_dir)
        except Exception:
            pass


def parse_epub(path: str) -> EpubResult:
    """Parse an EPUB ebook file.

    Extracts HTML chapters in reading order with metadata and images.

    Args:
        path: str — path to the EPUB file.

    Returns:
        dict with type, content, chapters list, metadata, images_dir.
    """
    error_result = {
        "type": "epub", "content": "",
        "title": "", "creator": "", "language": "",
        "chapters": [], "chapter_count": 0, "current_index": 0,
        "files": [], "images_dir": "", **file_meta(path),
    }

    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError) as e:
        return {**error_result, "content": f"[Bad EPUB file]: {e}"}

    try:
        names = zf.namelist()

        opf_path = None
        for name in names:
            if name.endswith("content.opf") or name.endswith(".opf"):
                opf_path = name
                break

        meta = {"title": "", "creator": "", "language": "", "spine": []}
        if opf_path:
            try:
                meta = _parse_opf(zf, opf_path)
            except Exception:
                pass

        opf_dir = ""
        if opf_path:
            opf_dir = "/".join(opf_path.split("/")[:-1])
            if opf_dir:
                opf_dir += "/"

        images_dir = _extract_images(zf, names, opf_dir)

        html_files = [n for n in names if n.endswith((".xhtml", ".html", ".htm"))]

        spine = meta["spine"]
        if spine:
            ordered = []
            for href in spine:
                full = opf_dir + href
                if full in html_files:
                    ordered.append(full)
            for h in html_files:
                if h not in ordered:
                    ordered.append(h)
            html_files = ordered

        chapters = []
        for h in html_files[:100]:
            try:
                with zf.open(h) as f:
                    raw = f.read().decode("utf-8", errors="replace")

                raw = _rewrite_image_paths(raw, images_dir, opf_dir)

                ch_title = ""
                m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
                if m:
                    ch_title = re.sub(r"<[^>]+>", "", m.group(1)).strip()

                chapters.append({
                    "href": h,
                    "html": raw,
                    "title": ch_title or h.split("/")[-1],
                })
            except Exception:
                continue

        content = ""
        if chapters:
            content = chapters[0]["html"]

        return {
            "type": "epub",
            "content": content,
            "title": meta["title"],
            "creator": meta["creator"],
            "language": meta["language"],
            "chapters": chapters,
            "chapter_count": len(chapters),
            "current_index": 0,
            "files": names,
            "images_dir": images_dir,
            **file_meta(path),
        }
    finally:
        zf.close()
