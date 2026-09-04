"""Base types and helpers for file metadata."""

import os
from typing import TypedDict


class FileMeta(TypedDict):
    """Common file metadata returned by all parsers.

    Attributes:
        path: Full file path.
        name: File name without directory.
        size: File size in bytes.
    """
    path: str
    name: str
    size: int


def file_meta(path: str) -> FileMeta:
    """Collect common file metadata.

    Args:
        path: Path to the file.

    Returns:
        FileMeta dict with path, name, and size.
    """
    return {
        "path": path,
        "name": os.path.basename(path),
        "size": os.path.getsize(path),
    }
