import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from integrations.media.video_compositor import VideoCompositionFailed, compose_voiceover_video


@patch("integrations.media.video_compositor.subprocess.run")
def test_compose_voiceover_video_calls_ffmpeg_and_returns_output(mock_run):
    def fake_run(cmd, **kwargs):
        Path(cmd[-1]).write_bytes(b"fake-mp4-bytes")
        return MagicMock(returncode=0)

    mock_run.side_effect = fake_run

    result = compose_voiceover_video(b"video-bytes", b"audio-bytes")

    assert result == b"fake-mp4-bytes"
    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "ffmpeg"
    assert "-stream_loop" in cmd
    assert "-shortest" in cmd


@patch("integrations.media.video_compositor.subprocess.run", side_effect=FileNotFoundError())
def test_compose_voiceover_video_raises_clear_error_when_ffmpeg_missing(mock_run):
    with pytest.raises(VideoCompositionFailed):
        compose_voiceover_video(b"video-bytes", b"audio-bytes")


@patch(
    "integrations.media.video_compositor.subprocess.run",
    side_effect=subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"boom"),
)
def test_compose_voiceover_video_raises_on_ffmpeg_failure(mock_run):
    with pytest.raises(VideoCompositionFailed):
        compose_voiceover_video(b"video-bytes", b"audio-bytes")


@patch(
    "integrations.media.video_compositor.subprocess.run",
    side_effect=subprocess.TimeoutExpired(["ffmpeg"], timeout=120),
)
def test_compose_voiceover_video_raises_clear_error_on_timeout(mock_run):
    with pytest.raises(VideoCompositionFailed):
        compose_voiceover_video(b"video-bytes", b"audio-bytes")
