import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.media import extract_media_metadata

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FFPROBE_SUCCESS_OUTPUT = json.dumps({
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
            "pix_fmt": "yuv420p",
            "duration": "10.5",
            "bit_rate": "4000000",
            "nb_frames": "315",
        },
        {
            "codec_type": "audio",
            "codec_name": "aac",
            "codec_long_name": "AAC (Advanced Audio Coding)",
            "sample_rate": "44100",
            "channels": 2,
            "duration": "10.5",
            "bit_rate": "128000",
        },
    ],
    "format": {
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "format_long_name": "QuickTime / MOV",
        "duration": "10.5",
        "size": "5242880",
        "bit_rate": "4124000",
        "nb_streams": 2,
    },
})


def _make_proc(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ---------------------------------------------------------------------------
# Success cases
# ---------------------------------------------------------------------------

class TestExtractMediaMetadataSuccess:
    def test_returns_format_fields(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=FFPROBE_SUCCESS_OUTPUT)
            result = extract_media_metadata(str(video_file))

        assert result["format_name"] == "mov,mp4,m4a,3gp,3g2,mj2"
        assert result["format_long_name"] == "QuickTime / MOV"
        assert result["duration"] == pytest.approx(10.5)
        assert result["size"] == 5242880
        assert result["bit_rate"] == 4124000
        assert result["nb_streams"] == 2

    def test_returns_video_stream(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=FFPROBE_SUCCESS_OUTPUT)
            result = extract_media_metadata(str(video_file))

        assert "video_streams" in result
        vs = result["video_streams"][0]
        assert vs["codec_name"] == "h264"
        assert vs["width"] == 1920
        assert vs["height"] == 1080
        assert vs["pix_fmt"] == "yuv420p"
        assert vs["r_frame_rate"] == "30/1"
        assert vs["duration"] == pytest.approx(10.5)
        assert vs["bit_rate"] == 4000000
        assert vs["nb_frames"] == "315"

    def test_returns_audio_stream(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=FFPROBE_SUCCESS_OUTPUT)
            result = extract_media_metadata(str(video_file))

        assert "audio_streams" in result
        as_ = result["audio_streams"][0]
        assert as_["codec_name"] == "aac"
        assert as_["sample_rate"] == "44100"
        assert as_["channels"] == 2
        assert as_["bit_rate"] == 128000

    def test_no_streams_keys_omitted_when_empty(self, tmp_path: Path) -> None:
        """video_streams / audio_streams keys absent when ffprobe reports no streams."""
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        output = json.dumps({
            "streams": [],
            "format": {
                "format_name": "mp4",
                "format_long_name": "MP4",
                "duration": "5.0",
                "size": "1024",
                "bit_rate": "1000",
                "nb_streams": 0,
            },
        })

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=output)
            result = extract_media_metadata(str(video_file))

        assert "video_streams" not in result
        assert "audio_streams" not in result

    def test_optional_numeric_fields_none_when_absent(self, tmp_path: Path) -> None:
        """duration / bit_rate are None when ffprobe omits them."""
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        output = json.dumps({
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "vp9",
                    "width": 640,
                    "height": 360,
                }
            ],
            "format": {
                "format_name": "webm",
                "nb_streams": 1,
            },
        })

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=output)
            result = extract_media_metadata(str(video_file))

        assert result["duration"] is None
        assert result["bit_rate"] is None
        assert result["video_streams"][0]["duration"] is None
        assert result["video_streams"][0]["bit_rate"] is None

    def test_correct_ffprobe_command_invoked(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout=FFPROBE_SUCCESS_OUTPUT)
            extract_media_metadata(str(video_file))

        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "ffprobe"
        assert "-print_format" in cmd
        assert "json" in cmd
        assert "-show_streams" in cmd
        assert "-show_format" in cmd
        assert cmd[-1] == str(video_file)
        assert kwargs.get("capture_output") is True
        assert kwargs.get("text") is True
        assert kwargs.get("timeout") == 60


# ---------------------------------------------------------------------------
# Failure cases
# ---------------------------------------------------------------------------

class TestExtractMediaMetadataFailure:
    def test_raises_file_not_found_for_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError, match="File not found"):
            extract_media_metadata("/nonexistent/path/video.mp4")

    def test_raises_runtime_error_on_nonzero_exit(self, tmp_path: Path) -> None:
        video_file = tmp_path / "corrupt.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(
                1, stderr="Invalid data found when processing input"
            )
            with pytest.raises(RuntimeError, match="ffprobe failed"):
                extract_media_metadata(str(video_file))

    def test_runtime_error_message_includes_stderr(self, tmp_path: Path) -> None:
        video_file = tmp_path / "corrupt.mp4"
        video_file.write_bytes(b"\x00")

        stderr_msg = "moov atom not found"
        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(1, stderr=stderr_msg)
            with pytest.raises(RuntimeError, match=stderr_msg):
                extract_media_metadata(str(video_file))

    def test_raises_on_invalid_json_output(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.return_value = _make_proc(0, stdout="not valid json{{")
            with pytest.raises(json.JSONDecodeError):
                extract_media_metadata(str(video_file))

    def test_propagates_subprocess_timeout(self, tmp_path: Path) -> None:
        video_file = tmp_path / "sample.mp4"
        video_file.write_bytes(b"\x00")

        with patch("app.media.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=60)
            with pytest.raises(subprocess.TimeoutExpired):
                extract_media_metadata(str(video_file))

