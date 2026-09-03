from typing import TypedDict
from ._meta import FileMeta, file_meta


class ImageExtResult(FileMeta):
    """Parsed extended image file metadata."""
    type: str
    content: str
    format: str
    width: int
    height: int
    mode: str
    info: dict[str, str]
    frames: int


def parse_image_ext(path: str) -> ImageExtResult:
    """Parse an image file (.gif, .bmp, .webp, .tiff) using Pillow.

    Extends parse_image with frame count for animated formats.

    Args:
        path: str — path to the image file.

    Returns:
        dict: {
            "type": str — always "image",
            "content": str — formatted image metadata,
            "format": str — image format,
            "width": int — width in pixels,
            "height": int — height in pixels,
            "mode": str — color mode,
            "info": dict[str, str] — extra metadata,
            "frames": int — number of frames (1 for static),
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        from PIL import Image
    except ImportError:
        return {
            "type": "image", "content": "[Pillow not installed]",
            "format": "", "width": 0, "height": 0, "mode": "",
            "info": {}, "frames": 0, **file_meta(path),
        }

    img = Image.open(path)
    w, h = img.size
    fmt = img.format or "unknown"
    mode = img.mode

    frames = 1
    try:
        frames = getattr(img, "n_frames", 1)
    except Exception:
        pass

    info: dict[str, str] = {}
    for k, v in img.info.items():
        if isinstance(v, (str, int, float)):
            info[k] = str(v)

    img.close()

    lines = [
        f"Format: {fmt}",
        f"Size: {w} x {h}",
        f"Mode: {mode}",
        f"Frames: {frames}",
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
        "frames": frames,
        **file_meta(path),
    }
