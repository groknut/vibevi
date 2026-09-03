import json
import subprocess
from typing import TypedDict
from ._meta import FileMeta, file_meta


class VideoResult(FileMeta):
    """Parsed video file metadata."""
    type: str
    content: str
    format_name: str
    duration: float
    width: int
    height: int
    codec: str
    bit_rate: int
    fps: float
    audio_codec: str
    audio_channels: int
    audio_sample_rate: int


def _ffprobe(path: str) -> dict:
    """Run ffprobe and return parsed JSON output."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def parse_video(path: str) -> VideoResult:
    """Parse a video file (.mp4, .avi, .mkv, etc.) using ffprobe.

    Extracts format, duration, resolution, codecs, bit rate, and FPS.

    Args:
        path: str — path to the video file.

    Returns:
        dict: {
            "type": str — always "video",
            "content": str — formatted metadata summary,
            "format_name": str — container format (e.g. "mov,mp4"),
            "duration": float — duration in seconds,
            "width": int — video width in pixels,
            "height": int — video height in pixels,
            "codec": str — video codec name,
            "bit_rate": int — overall bit rate in bps,
            "fps": float — frames per second,
            "audio_codec": str — audio codec name,
            "audio_channels": int — number of audio channels,
            "audio_sample_rate": int — audio sample rate in Hz,
            "path": str — full file path,
            "name": str — file name only,
            "size": int — file size in bytes,
        }
    """
    try:
        data = _ffprobe(path)
    except FileNotFoundError:
        return {
            "type": "video", "content": "[ffprobe not installed]",
            "format_name": "", "duration": 0, "width": 0, "height": 0,
            "codec": "", "bit_rate": 0, "fps": 0,
            "audio_codec": "", "audio_channels": 0, "audio_sample_rate": 0,
            **file_meta(path),
        }

    fmt = data.get("format", {})
    video_stream = None
    audio_stream = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and video_stream is None:
            video_stream = s
        elif s.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = s

    duration = float(fmt.get("duration", 0))
    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0
    codec = video_stream.get("codec_name", "") if video_stream else ""
    bit_rate = int(fmt.get("bit_rate", 0))

    fps = 0.0
    if video_stream:
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        parts = r_frame_rate.split("/")
        if len(parts) == 2 and int(parts[1]) != 0:
            fps = round(int(parts[0]) / int(parts[1]), 2)

    audio_codec = audio_stream.get("codec_name", "") if audio_stream else ""
    audio_channels = int(audio_stream.get("channels", 0)) if audio_stream else 0
    audio_sample_rate = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0

    lines = [
        f"Format: {fmt.get('format_long_name', fmt.get('format_name', ''))}",
        f"Duration: {duration:.2f}s",
        f"Resolution: {width} x {height}",
        f"Video codec: {codec}",
        f"FPS: {fps}",
        f"Bit rate: {bit_rate} bps",
        f"Audio codec: {audio_codec}",
        f"Audio channels: {audio_channels}",
        f"Audio sample rate: {audio_sample_rate} Hz",
    ]

    return {
        "type": "video",
        "content": "\n".join(lines),
        "format_name": fmt.get("format_name", ""),
        "duration": duration,
        "width": width,
        "height": height,
        "codec": codec,
        "bit_rate": bit_rate,
        "fps": fps,
        "audio_codec": audio_codec,
        "audio_channels": audio_channels,
        "audio_sample_rate": audio_sample_rate,
        **file_meta(path),
    }
