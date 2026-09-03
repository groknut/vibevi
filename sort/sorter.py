import os
from pathlib import Path
from enum import Enum
from typing import TypedDict


class SortKey(Enum):
    """Available sort parameters."""
    NAME = "name"
    DATE = "date"
    EXTENSION = "extension"


class FileEntry(TypedDict):
    """Single file entry with metadata."""
    path: str
    name: str
    size: int
    extension: str
    date: float
    is_dir: bool


def scan_directory(path: str, recursive: bool = False) -> list[FileEntry]:
    """Scan a directory and collect file and directory entries.

    Args:
        path: str — directory path to scan.
        recursive: bool — if True, scan subdirectories recursively.

    Returns:
        list[FileEntry] — list of file and directory entries.
    """
    dir_path = Path(path)
    if not dir_path.is_dir():
        return []

    entries: list[FileEntry] = []
    pattern = "**/*" if recursive else "*"

    for item in dir_path.glob(pattern):
        if item.name.startswith("."):
            continue

        full_path = str(item)
        stat = item.stat()
        is_dir = item.is_dir()

        entries.append({
            "path": full_path,
            "name": item.name,
            "size": stat.st_size if not is_dir else 0,
            "extension": item.suffix.lower() if not is_dir else "",
            "date": stat.st_ctime,
            "is_dir": is_dir,
        })

    return entries


def sort_files(
    path: str,
    sort_by: SortKey = SortKey.NAME,
    reverse: bool = False,
    recursive: bool = False,
) -> list[FileEntry]:
    """Scan a directory and sort files and directories.

    Directories always appear before files within each sort group.

    Args:
        path: str — directory path to scan.
        sort_by: SortKey — NAME (alphabetical), DATE (creation time), EXTENSION (by file extension).
        reverse: bool — if True, sort in descending order.
        recursive: bool — if True, include files from subdirectories.

    Returns:
        list[FileEntry] — sorted list of file and directory entries.
    """
    entries = scan_directory(path, recursive=recursive)

    def sort_key(e: FileEntry):
        name = e["name"].lower()
        if sort_by == SortKey.NAME:
            return (0 if e["is_dir"] else 1, name)
        elif sort_by == SortKey.DATE:
            return (0 if e["is_dir"] else 1, e["date"], name)
        elif sort_by == SortKey.EXTENSION:
            return (0 if e["is_dir"] else 1, e["extension"], name)
        return (0 if e["is_dir"] else 1, name)

    entries.sort(key=sort_key, reverse=reverse)

    return entries
