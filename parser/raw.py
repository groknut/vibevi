from typing import TypedDict
from ._meta import FileMeta, file_meta

MAX_RAW_SIZE = 10 * 1024 * 1024  # 10MB


class RawResult(FileMeta):
    type: str
    content: str
    hex_content: str
    truncated: bool


def parse_raw(path: str) -> RawResult:
    size = file_meta(path)["size"]
    truncated = size > MAX_RAW_SIZE

    with open(path, "rb") as f:
        data = f.read(MAX_RAW_SIZE)

    text = data.decode("utf-8", errors="replace")

    preview_size = min(len(data), 512)
    hex_lines: list[str] = []
    for offset in range(0, preview_size, 16):
        chunk = data[offset:offset + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        hex_lines.append(f"{offset:08x}  {hex_part:<48s}  {ascii_part}")

    hex_content = "\n".join(hex_lines)
    if truncated:
        hex_content += f"\n\n[Truncated: showing first {MAX_RAW_SIZE} bytes of {size} total]"

    return {
        "type": "raw",
        "content": text,
        "hex_content": hex_content,
        "truncated": truncated,
        **file_meta(path),
    }
