import zipfile
import re
from xml.etree import ElementTree as ET
from typing import TypedDict
from ._meta import FileMeta, file_meta


class EpubResult(FileMeta):
    """Parsed EPUB file metadata."""
    type: str
    content: str
    title: str
    creator: str
    language: str
    chapters: list[dict]
    chapter_count: int
    current_index: int
    files: list[str]


def _parse_opf(zf: zipfile.ZipFile, opf_path: str) -> dict:
    """Parse content.opf to extract metadata and spine order."""
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


def parse_epub(path: str) -> EpubResult:
    """Parse an EPUB ebook file.

    Extracts HTML chapters in reading order with metadata.

    Args:
        path: str — path to the EPUB file.

    Returns:
        dict with type, content (current chapter HTML), chapters list, metadata.
    """
    error_result = {
        "type": "epub", "content": "",
        "title": "", "creator": "", "language": "",
        "chapters": [], "chapter_count": 0, "current_index": 0,
        "files": [], **file_meta(path),
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
            **file_meta(path),
        }
    finally:
        zf.close()
