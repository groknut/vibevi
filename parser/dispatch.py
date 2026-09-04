"""Central dispatch: maps file extensions to parser functions."""

from pathlib import Path
from typing import Callable
from ._meta import file_meta
from .text import parse_txt, parse_log
from .markdown import parse_md
from .data import parse_json, parse_xml
from .csv import parse_csv
from .yaml import parse_yaml
from .html import parse_html
from .svg import parse_svg
from .code import parse_code
from .config import parse_ini, parse_properties
from .toml import parse_toml
from .document import parse_pdf, parse_docx
from .spreadsheet import parse_xlsx, parse_xls
from .image import parse_image
from .image_ext import parse_image_ext
from .video import parse_video
from .audio import parse_audio
from .audio_ext import parse_audio_ext
from .archive import parse_zip, parse_tar, parse_7z, parse_rar
from .epub import parse_epub
from .raw import parse_raw


PARSERS: dict[str, Callable[[str], dict]] = {
    # text
    ".txt": parse_txt,
    ".md": parse_md,
    ".log": parse_log,
    # data
    ".json": parse_json,
    ".xml": parse_xml,
    ".csv": parse_csv,
    ".yaml": parse_yaml,
    ".yml": parse_yaml,
    ".toml": parse_toml,
    # markup
    ".html": parse_html,
    ".htm": parse_html,
    ".svg": parse_svg,
    # source code
    ".py": parse_code, ".pyw": parse_code,
    ".js": parse_code, ".mjs": parse_code, ".cjs": parse_code,
    ".ts": parse_code, ".mts": parse_code, ".cts": parse_code,
    ".jsx": parse_code, ".tsx": parse_code,
    ".c": parse_code, ".h": parse_code,
    ".cpp": parse_code, ".cxx": parse_code, ".cc": parse_code,
    ".hpp": parse_code, ".hxx": parse_code,
    ".java": parse_code,
    ".go": parse_code,
    ".rs": parse_code,
    ".rb": parse_code,
    ".php": parse_code,
    ".swift": parse_code,
    ".kt": parse_code, ".kts": parse_code,
    ".r": parse_code, ".R": parse_code,
    ".pl": parse_code, ".pm": parse_code,
    ".lua": parse_code,
    ".sh": parse_code, ".bash": parse_code, ".zsh": parse_code,
    ".bat": parse_code, ".cmd": parse_code,
    ".ps1": parse_code,
    ".cs": parse_code,
    ".fs": parse_code, ".fsx": parse_code,
    ".scala": parse_code,
    ".dart": parse_code,
    ".ex": parse_code, ".exs": parse_code,
    ".erl": parse_code,
    ".hs": parse_code,
    ".ml": parse_code, ".mli": parse_code,
    ".clj": parse_code,
    ".lisp": parse_code, ".el": parse_code,
    ".vim": parse_code,
    ".sql": parse_code,
    ".graphql": parse_code, ".gql": parse_code,
    ".proto": parse_code,
    ".tf": parse_code, ".hcl": parse_code,
    # config
    ".ini": parse_ini, ".cfg": parse_ini, ".conf": parse_ini,
    ".properties": parse_properties,
    # documents
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".xls": parse_xls,
    ".epub": parse_epub,
    # images
    ".png": parse_image,
    ".jpeg": parse_image,
    ".jpg": parse_image,
    ".gif": parse_image_ext,
    ".bmp": parse_image_ext,
    ".webp": parse_image_ext,
    ".tiff": parse_image_ext,
    ".tif": parse_image_ext,
    # video
    ".mp4": parse_video,
    ".avi": parse_video,
    ".mkv": parse_video,
    ".mov": parse_video,
    ".wmv": parse_video,
    ".flv": parse_video,
    ".webm": parse_video,
    ".m4v": parse_video,
    # audio
    ".mp3": parse_audio,
    ".wav": parse_audio,
    ".m4a": parse_audio,
    ".ogg": parse_audio_ext,
    ".flac": parse_audio_ext,
    ".aac": parse_audio_ext,
    # archives
    ".zip": parse_zip,
    ".tar": parse_tar,
    ".tar.gz": parse_tar,
    ".tgz": parse_tar,
    ".tar.bz2": parse_tar,
    ".tbz2": parse_tar,
    ".tar.xz": parse_tar,
    ".txz": parse_tar,
    ".7z": parse_7z,
    ".rar": parse_rar,
}


def parse_file(path: str) -> dict:
    """Dispatch to the appropriate parser by file extension.

    Falls back to parse_raw for unsupported extensions.
    Returns type="error" on parser failure.
    """
    ext = Path(path).suffix.lower()

    compound_ext = ""
    parts = Path(path).name.lower().split(".")
    if len(parts) >= 3:
        compound_ext = f".{parts[-2]}.{parts[-1]}"

    parser = PARSERS.get(compound_ext) or PARSERS.get(ext)

    if parser is None:
        try:
            return parse_raw(path)
        except Exception as e:
            return {"type": "error", "content": f"[Error reading raw file]: {e}", **file_meta(path)}

    try:
        return parser(path)
    except Exception as e:
        return {"type": "error", "content": f"[Error parsing {ext}]: {e}", **file_meta(path)}
