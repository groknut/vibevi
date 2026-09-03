import os
import tarfile
import zipfile
from typing import TypedDict
from ._meta import FileMeta, file_meta


class ArchiveResult(FileMeta):
    """Parsed archive file metadata."""
    type: str
    content: str
    files: list[str]
    count: int
    archive_type: str


def parse_zip(path: str) -> ArchiveResult:
    """Parse a ZIP archive.

    Args:
        path: str — path to the ZIP file.

    Returns:
        dict: {
            "type": str — always "archive",
            "content": str — file listing with sizes,
            "files": list[str] — all file paths inside,
            "count": int — number of entries,
            "archive_type": str — "zip",
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        with zipfile.ZipFile(path, "r") as zf:
            entries = zf.infolist()
    except zipfile.BadZipFile as e:
        return {
            "type": "archive", "content": f"[Bad ZIP file]: {e}",
            "files": [], "count": 0, "archive_type": "zip", **file_meta(path),
        }

    files = [e.filename for e in entries]
    total_size = sum(e.file_size for e in entries)

    lines = [f"Entries: {len(entries)}", f"Total uncompressed size: {total_size:,} bytes", ""]
    for e in sorted(entries, key=lambda x: x.filename):
        ratio = f" ({e.compress_size}/{e.file_size})" if e.file_size else ""
        lines.append(f"  {e.filename}{ratio}")

    return {
        "type": "archive",
        "content": "\n".join(lines),
        "files": files,
        "count": len(entries),
        "archive_type": "zip",
        **file_meta(path),
    }


def _tar_type(path: str) -> str:
    """Detect tar compression type from extension."""
    lower = path.lower()
    if lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        return "tar.gz"
    elif lower.endswith(".tar.bz2") or lower.endswith(".tbz2"):
        return "tar.bz2"
    elif lower.endswith(".tar.xz") or lower.endswith(".txz"):
        return "tar.xz"
    return "tar"


def parse_tar(path: str) -> ArchiveResult:
    """Parse a TAR/TAR.GZ/TAR.BZ2/TAR.XZ archive.

    Args:
        path: str — path to the tar file.

    Returns:
        dict: {
            "type": str — always "archive",
            "content": str — file listing with sizes,
            "files": list[str] — all file paths inside,
            "count": int — number of entries,
            "archive_type": str — "tar", "tar.gz", "tar.bz2", or "tar.xz",
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    archive_type = _tar_type(path)

    try:
        with tarfile.open(path, "r:*") as tf:
            members = tf.getmembers()
    except (tarfile.TarError, EOFError) as e:
        return {
            "type": "archive", "content": f"[Bad tar file]: {e}",
            "files": [], "count": 0, "archive_type": archive_type, **file_meta(path),
        }

    files = [m.name for m in members if m.isfile()]
    total_size = sum(m.size for m in members)

    lines = [f"Type: {archive_type}", f"Entries: {len(members)}", f"Total size: {total_size:,} bytes", ""]
    for m in sorted(members, key=lambda x: x.name):
        kind = "dir" if m.isdir() else "file" if m.isfile() else "link"
        lines.append(f"  [{kind}] {m.name} ({m.size:,} bytes)")

    return {
        "type": "archive",
        "content": "\n".join(lines),
        "files": files,
        "count": len(members),
        "archive_type": archive_type,
        **file_meta(path),
    }
