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


def scan_directory(path: str, recursive: bool = False) -> list[FileEntry]:
    """Scan a directory and collect file entries.

    Args:
        path: str — directory path to scan.
        recursive: bool — if True, scan subdirectories recursively.

    Returns:
        list[FileEntry] — list of file entries.
    """
    dir_path = Path(path)
    if not dir_path.is_dir():
        return []

    entries: list[FileEntry] = []
    pattern = "**/*" if recursive else "*"

    for item in dir_path.glob(pattern):
        if not item.is_file():
            continue

        full_path = str(item)
        stat = item.stat()

        entries.append({
            "path": full_path,
            "name": item.name,
            "size": stat.st_size,
            "extension": item.suffix.lower(),
            "date": stat.st_ctime,
        })

    return entries


def sort_files(
    path: str,
    sort_by: SortKey = SortKey.NAME,
    reverse: bool = False,
    recursive: bool = False,
) -> list[FileEntry]:
    """Scan a directory and sort files.

    Args:
        path: str — directory path to scan.
        sort_by: SortKey — NAME (alphabetical), DATE (creation time), EXTENSION (by file extension).
        reverse: bool — if True, sort in descending order.
        recursive: bool — if True, include files from subdirectories.

    Returns:
        list[FileEntry] — sorted list of file entries.
    """
    entries = scan_directory(path, recursive=recursive)

    if sort_by == SortKey.NAME:
        entries.sort(key=lambda e: e["name"].lower(), reverse=reverse)
    elif sort_by == SortKey.DATE:
        entries.sort(key=lambda e: e["date"], reverse=reverse)
    elif sort_by == SortKey.EXTENSION:
        entries.sort(key=lambda e: (e["extension"], e["name"].lower()), reverse=reverse)

    return entries
