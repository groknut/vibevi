from typing import TypedDict
from ._meta import FileMeta, file_meta


class AudioExtResult(FileMeta):
    """Parsed extended audio file metadata."""
    type: str
    content: str
    format: str
    duration: float
    channels: int
    sample_rate: int
    bit_rate: int
    tags: dict[str, str]


def parse_audio_ext(path: str) -> AudioExtResult:
    """Parse an audio file (.ogg, .flac, .aac) using mutagen.

    Args:
        path: str — path to the audio file.

    Returns:
        dict: {
            "type": str — always "audio",
            "content": str — formatted audio metadata,
            "format": str — audio format name,
            "duration": float — duration in seconds,
            "channels": int — number of channels,
            "sample_rate": int — sample rate in Hz,
            "bit_rate": int — bit rate in bps,
            "tags": dict[str, str] — audio tags,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        import mutagen
    except ImportError:
        return {
            "type": "audio", "content": "[mutagen not installed]",
            "format": "", "duration": 0, "channels": 0,
            "sample_rate": 0, "bit_rate": 0, "tags": {}, **file_meta(path),
        }

    audio = mutagen.File(path)
    if audio is None:
        return {
            "type": "audio", "content": "[unrecognized audio format]",
            "format": "", "duration": 0, "channels": 0,
            "sample_rate": 0, "bit_rate": 0, "tags": {}, **file_meta(path),
        }

    info = audio.info
    duration = getattr(info, "length", 0.0)
    channels = getattr(info, "channels", 0)
    sample_rate = getattr(info, "sample_rate", 0)
    bit_rate = getattr(info, "bitrate", 0)

    tags: dict[str, str] = {}
    if audio.tags:
        for key, val in audio.tags.items():
            if hasattr(val, "text"):
                tags[key] = str(val.text[0]) if val.text else ""
            else:
                tags[key] = str(val)

    lines = [
        f"Format: {type(audio).__name__}",
        f"Duration: {duration:.2f}s",
        f"Channels: {channels}",
        f"Sample rate: {sample_rate} Hz",
        f"Bit rate: {bit_rate} bps",
    ]
    if tags:
        lines.append("Tags:")
        for k, v in tags.items():
            lines.append(f"  {k}: {v}")

    return {
        "type": "audio",
        "content": "\n".join(lines),
        "format": type(audio).__name__,
        "duration": duration,
        "channels": channels,
        "sample_rate": sample_rate,
        "bit_rate": bit_rate,
        "tags": tags,
        **file_meta(path),
    }
