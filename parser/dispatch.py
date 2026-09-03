from pathlib import Path
from typing import Callable
from ._meta import file_meta
from .text import parse_txt, parse_md, parse_log
from .data import parse_json, parse_xml
from .document import parse_pdf, parse_docx
from .spreadsheet import parse_xlsx, parse_xls
from .image import parse_image
from .raw import parse_raw


PARSERS: dict[str, Callable[[str], dict]] = {
    ".txt": parse_txt,
    ".md": parse_md,
    ".log": parse_log,
    ".json": parse_json,
    ".xml": parse_xml,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
    ".xls": parse_xls,
    ".png": parse_image,
    ".jpeg": parse_image,
    ".jpg": parse_image,
}


def parse_file(path: str) -> dict:
    """Dispatch to the appropriate parser by file extension.

    Falls back to parse_raw for unsupported extensions.
    Returns type="error" on parser failure.
    """
    ext = Path(path).suffix.lower()
    parser = PARSERS.get(ext)

    if parser is None:
        try:
            return parse_raw(path)
        except Exception as e:
            return {"type": "error", "content": f"[Error reading raw file]: {e}", **file_meta(path)}

    try:
        return parser(path)
    except Exception as e:
        return {"type": "error", "content": f"[Error parsing {ext}]: {e}", **file_meta(path)}
