import json
import subprocess
from pathlib import Path


def extract_media_metadata(file_path: str) -> dict:
    """Run ffprobe on the given file and return parsed metadata."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    raw = json.loads(result.stdout)
    metadata: dict = {}

    fmt = raw.get("format", {})
    if fmt:
        metadata["format_name"] = fmt.get("format_name")
        metadata["format_long_name"] = fmt.get("format_long_name")
        metadata["duration"] = float(fmt["duration"]) if fmt.get("duration") else None
        metadata["size"] = int(fmt["size"]) if fmt.get("size") else None
        metadata["bit_rate"] = int(fmt["bit_rate"]) if fmt.get("bit_rate") else None
        metadata["nb_streams"] = fmt.get("nb_streams")

    video_streams = []
    audio_streams = []

    for stream in raw.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video":
            video_streams.append({
                "codec_name": stream.get("codec_name"),
                "codec_long_name": stream.get("codec_long_name"),
                "width": stream.get("width"),
                "height": stream.get("height"),
                "r_frame_rate": stream.get("r_frame_rate"),
                "avg_frame_rate": stream.get("avg_frame_rate"),
                "pix_fmt": stream.get("pix_fmt"),
                "duration": float(stream["duration"]) if stream.get("duration") else None,
                "bit_rate": int(stream["bit_rate"]) if stream.get("bit_rate") else None,
                "nb_frames": stream.get("nb_frames"),
            })
        elif codec_type == "audio":
            audio_streams.append({
                "codec_name": stream.get("codec_name"),
                "codec_long_name": stream.get("codec_long_name"),
                "sample_rate": stream.get("sample_rate"),
                "channels": stream.get("channels"),
                "duration": float(stream["duration"]) if stream.get("duration") else None,
                "bit_rate": int(stream["bit_rate"]) if stream.get("bit_rate") else None,
            })

    if video_streams:
        metadata["video_streams"] = video_streams
    if audio_streams:
        metadata["audio_streams"] = audio_streams

    return metadata
