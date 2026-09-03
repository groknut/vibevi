import zipfile
from typing import TypedDict
from ._meta import FileMeta, file_meta


class EpubResult(FileMeta):
    """Parsed EPUB file metadata."""
    type: str
    content: str
    title: str
    creator: str
    language: str
    chapters: int
    files: list[str]


def parse_epub(path: str) -> EpubResult:
    """Parse an EPUB ebook file.

    EPUB is a ZIP archive containing XHTML content and metadata.

    Args:
        path: str — path to the EPUB file.

    Returns:
        dict: {
            "type": str — always "epub",
            "content": str — extracted text content,
            "title": str — book title,
            "creator": str — author,
            "language": str — language code,
            "chapters": int — number of XHTML chapter files,
            "files": list[str] — all files in archive,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as e:
        return {
            "type": "epub", "content": f"[Bad EPUB file]: {e}",
            "title": "", "creator": "", "language": "",
            "chapters": 0, "files": [], **file_meta(path),
        }

    meta = {"title": "", "creator": "", "language": ""}
    try:
        for name in names:
            if name.endswith("content.opf") or name.endswith("opf"):
                with zf.open(name) as f:
                    opf = f.read().decode("utf-8", errors="replace")
                for tag, key in [("dc:title", "title"), ("dc:creator", "creator"), ("dc:language", "language")]:
                    start = opf.find(f"<{tag}")
                    if start == -1:
                        continue
                    end_close = opf.find(">", start)
                    end_tag = opf.find(f"</{tag}", end_close)
                    if end_tag != -1:
                        meta[key] = opf[end_close + 1:end_tag].strip()
                break
    except Exception:
        pass

    chapter_files = [n for n in names if n.endswith((".xhtml", ".html", ".htm"))]
    text_parts: list[str] = []
    for ch in chapter_files[:50]:
        try:
            with zf.open(ch) as f:
                content = f.read().decode("utf-8", errors="replace")
            import re
            clean = re.sub(r"<[^>]+>", " ", content)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                text_parts.append(f"--- {ch} ---\n{clean}")
        except Exception:
            continue

    full_text = "\n\n".join(text_parts)
    if len(chapter_files) > 50:
        full_text += f"\n\n... ({len(chapter_files) - 50} more chapters)"

    lines = [
        f"Title: {meta['title'] or '(none)'}",
        f"Author: {meta['creator'] or '(none)'}",
        f"Language: {meta['language'] or '(none)'}",
        f"Chapters: {len(chapter_files)}",
        f"Total files: {len(names)}",
        "",
        "--- Content ---",
        full_text[:10000] if full_text else "(no text content extracted)",
    ]
    if len(full_text) > 10000:
        lines.append(f"\n... ({len(full_text) - 10000} more chars)")

    return {
        "type": "epub",
        "content": "\n".join(lines),
        "title": meta["title"],
        "creator": meta["creator"],
        "language": meta["language"],
        "chapters": len(chapter_files),
        "files": names,
        **file_meta(path),
    }
