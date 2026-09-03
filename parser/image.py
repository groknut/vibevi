from typing import TypedDict
from ._meta import FileMeta, file_meta


class ImageResult(FileMeta):
    type: str
    content: str
    format: str
    width: int
    height: int
    mode: str
    info: dict[str, str]


def parse_image(path: str) -> ImageResult:
    """Parse an image file using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        return {"type": "image", "content": "[Pillow not installed]", "format": "", "width": 0, "height": 0, "mode": "", "info": {}, **file_meta(path)}

    img = Image.open(path)
    w, h = img.size
    fmt = img.format or "unknown"
    mode = img.mode

    info: dict[str, str] = {}
    for k, v in img.info.items():
        if isinstance(v, (str, int, float)):
            info[k] = str(v)

    img.close()

    lines = [
        f"Format: {fmt}",
        f"Size: {w} x {h}",
        f"Mode: {mode}",
    ]
    for k, v in info.items():
        lines.append(f"{k}: {v}")

    return {
        "type": "image",
        "content": "\n".join(lines),
        "format": fmt,
        "width": w,
        "height": h,
        "mode": mode,
        "info": info,
        **file_meta(path),
    }
