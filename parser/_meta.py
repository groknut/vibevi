import os
from typing import TypedDict


class FileMeta(TypedDict):
    path: str
    name: str
    size: int


def file_meta(path: str) -> FileMeta:
    """Collect common file metadata."""
    return {
        "path": path,
        "name": os.path.basename(path),
        "size": os.path.getsize(path),
    }
