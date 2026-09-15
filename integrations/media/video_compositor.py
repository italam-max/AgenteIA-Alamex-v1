import subprocess
import tempfile
from pathlib import Path


_FFMPEG_TIMEOUT_SECONDS = 120


class VideoCompositionFailed(Exception):
    pass


def compose_voiceover_video(video_bytes: bytes, audio_bytes: bytes) -> bytes:
    """
    Loops `video_bytes` (a short silent b-roll clip) to cover the full length of `audio_bytes`
    (the narration) and muxes them into one mp4 — the standard "voiceover over looping b-roll"
    pattern for short-form video. Requires the `ffmpeg` binary on PATH (see README setup).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = Path(tmp_dir) / "video.mp4"
        audio_path = Path(tmp_dir) / "audio.mp3"
        output_path = Path(tmp_dir) / "output.mp4"
        video_path.write_bytes(video_bytes)
        audio_path.write_bytes(audio_bytes)

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-stream_loop",
                    "-1",
                    "-i",
                    str(video_path),
                    "-i",
                    str(audio_path),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-shortest",
                    str(output_path),
                ],
                capture_output=True,
                check=True,
                timeout=_FFMPEG_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise VideoCompositionFailed(
                "ffmpeg no está instalado o no está en PATH — necesario para unir video y voz. Ver README."
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
            raise VideoCompositionFailed(f"ffmpeg failed: {stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise VideoCompositionFailed(
                f"ffmpeg no terminó en {_FFMPEG_TIMEOUT_SECONDS}s (posible input corrupto) — abortado."
            ) from exc

        return output_path.read_bytes()
