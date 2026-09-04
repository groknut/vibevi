"""Audio file parser using stdlib wave and mutagen for metadata."""

import struct
import wave
from typing import TypedDict
from ._meta import FileMeta, file_meta


class AudioResult(FileMeta):
    """Parsed audio file metadata.

    Attributes:
        type: Always "audio".
        content: Formatted audio info string.
        format: Audio format name.
        duration: Duration in seconds.
        channels: Number of audio channels.
        sample_rate: Sample rate in Hz.
        bit_rate: Bit rate in bps.
        bits_per_sample: Bits per sample.
        tags: Audio metadata tags.
    """
    type: str
    content: str
    format: str
    duration: float
    channels: int
    sample_rate: int
    bit_rate: int
    bits_per_sample: int
    tags: dict[str, str]


def _parse_wav(path: str) -> dict:
    """Parse WAV file metadata using stdlib wave module.

    Args:
        path: Path to the WAV file.

    Returns:
        Dict with audio metadata.
    """
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        bits = wf.getsampwidth() * 8
        frames = wf.getnframes()
        duration = frames / sample_rate if sample_rate else 0.0

    return {
        "format": "wav",
        "duration": duration,
        "channels": channels,
        "sample_rate": sample_rate,
        "bit_rate": sample_rate * channels * (bits // 8) * 8,
        "bits_per_sample": bits,
        "tags": {},
    }


def _parse_with_mutagen(path: str) -> dict:
    """Parse audio metadata using mutagen library.

    Args:
        path: Path to the audio file.

    Returns:
        Dict with audio metadata.
    """
    import mutagen

    audio = mutagen.File(path)
    if audio is None:
        return {"format": "", "duration": 0, "channels": 0, "sample_rate": 0,
                "bit_rate": 0, "bits_per_sample": 0, "tags": {}}

    info = audio.info
    duration = getattr(info, "length", 0.0)
    channels = getattr(info, "channels", 0)
    sample_rate = getattr(info, "sample_rate", 0)
    bit_rate = getattr(info, "bitrate", 0)
    bits_per_sample = getattr(info, "bits_per_sample", 0)

    tags: dict[str, str] = {}
    if audio.tags:
        for key, val in audio.tags.items():
            if hasattr(val, "text"):
                tags[key] = str(val.text[0]) if val.text else ""
            else:
                tags[key] = str(val)

    return {
        "format": type(audio).__name__.lower(),
        "duration": duration,
        "channels": channels,
        "sample_rate": sample_rate,
        "bit_rate": bit_rate,
        "bits_per_sample": bits_per_sample,
        "tags": tags,
    }


def parse_audio(path: str) -> AudioResult:
    """Parse an audio file (WAV, MP3, M4A).

    Uses stdlib wave for WAV files, mutagen for others.

    Args:
        path: Path to the audio file.

    Returns:
        AudioResult with format, duration, and tag info.
    """
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext == "wav":
        try:
            meta = _parse_wav(path)
        except Exception:
            meta = _parse_with_mutagen(path)
    else:
        meta = _parse_with_mutagen(path)

    lines = [
        f"Format: {meta['format']}",
        f"Duration: {meta['duration']:.2f}s",
        f"Channels: {meta['channels']}",
        f"Sample rate: {meta['sample_rate']} Hz",
        f"Bit rate: {meta['bit_rate']} bps",
        f"Bits per sample: {meta['bits_per_sample']}",
    ]

    if meta["tags"]:
        lines.append("Tags:")
        for k, v in meta["tags"].items():
            lines.append(f"  {k}: {v}")

    return {
        "type": "audio",
        "content": "\n".join(lines),
        **meta,
        **file_meta(path),
    }
