"""LocalClip: free local auto-clipping for Windows, using CPU Whisper + FFmpeg."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from core import select_highlights, video_filter, write_srt


def command(arguments: list[str], cwd: Path | None = None) -> str:
    process = subprocess.run(
        arguments, cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", check=False,
    )
    if process.returncode:
        raise RuntimeError(
            f"Command failed ({process.returncode}): {arguments[0]}\n"
            f"{process.stderr[-2500:]}"
        )
    return process.stdout


def duration_of(path: Path) -> float:
    result = command([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]).strip()
    try:
        duration = float(result)
    except ValueError as exc:
        raise RuntimeError("Cannot read video duration. Try a supported MP4/MOV/WebM file.") from exc
    if not 0 < duration < 24 * 3600:
        raise RuntimeError("Video duration must be greater than zero and under 24 hours.")
    return duration


def acquire_video(mode: str, url: str, local_path: str, uploaded, work: Path) -> Path:
    if mode == "Video URL":
        if not url.strip().lower().startswith(("https://", "http://")):
            raise ValueError("Enter an http:// or https:// video URL.")
        from yt_dlp import YoutubeDL

        options = {
            "outtmpl": str(work / "source.%(ext)s"),
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
        }
        with YoutubeDL(options) as loader:
            loader.download([url.strip()])
        media = [
            p for p in work.glob("source.*")
            if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm", ".m4v")
        ]
        if not media:
            raise RuntimeError("The link could not be downloaded as a video.")
        return max(media, key=lambda p: p.stat().st_size)

    if mode == "Local file path":
        path = Path(local_path.strip().strip('"')).expanduser()
        if not path.is_file():
            raise ValueError("The local file path does not exist.")
        return path.resolve()

    if uploaded is None:
        raise ValueError("Choose a video file to upload.")
    extension = Path(uploaded.name).suffix.lower()
    if extension not in (".mp4", ".mov", ".mkv", ".webm", ".m4v"):
        raise ValueError("Choose MP4, MOV, MKV, WebM or M4V.")
    target = work / ("source" + extension)
    with target.open("wb") as out:
        while True:
            chunk = uploaded.read(8 * 1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    return target


def transcribe(path: Path, model_size: str) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    fragments, _ = model.transcribe(
        str(path), beam_size=1, vad_filter=True, condition_on_previous_text=False
    )
    return [
        {"start": float(f.start), "end": float(f.end), "text": f.text.strip()}
        for f in fragments
        if f.end > f.start
    ]


def render_clips(
    source: Path, work: Path, segments: list[dict],
    choices: list[dict], aspect: str, captions: bool, style: str,
) -> bytes:
    output = io.BytesIO()
    progress = st.progress(0, text="Rendering clips locally...")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, clip in enumerate(choices, 1):
            srt_name = f"captions_{index:02}.srt"
            subtitle_count = write_srt(
                segments, clip["start"], clip["end"], work / srt_name
            )
            filtergraph = video_filter(
                aspect,
                srt_name if captions and subtitle_count else None,
                style,
            )
            dest = work / f"clip_{index:02}.mp4"
            command([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", str(clip["start"]), "-i", str(source),
                "-t", str(clip["end"] - clip["start"]),
                "-vf", filtergraph,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(dest),
            ], cwd=work)
            archive.write(dest, dest.name)
            progress.progress(index / len(choices), text=f"Rendered {index}/{len(choices)}")
        archive.writestr(
            "clip_details.json",
            json.dumps({"clips": choices, "aspect_ratio": aspect}, indent=2),
        )
    return output.getvalue()


st.set_page_config(page_title="LocalClip — Free Video Clipper", page_icon="✂️")
st.title("✂️ LocalClip")
st.caption("Free, local, no Docker and no API key. Clips are generated on your PC.")
st.info(
    "This is an original starter app, not ScaleReach or OpenShorts. "
    "It uses local speech transcription and heuristic highlight ranking; "
    "the score is not a prediction of virality."
)

with st.form("generate"):
    mode = st.radio(
        "Video source", ["Video URL", "Local file path", "Upload video"],
        horizontal=True,
    )
    url = st.text_input("Video link (YouTube or another supported site)") if mode == "Video URL" else ""
    local_path = st.text_input("Full local video path (best for large files)") if mode == "Local file path" else ""
    uploaded = (
        st.file_uploader("Video file", type=["mp4", "mov", "mkv", "webm", "m4v"])
        if mode == "Upload video" else None
    )
    left, right = st.columns(2)
    with left:
        count = st.slider("Number of clips", 1, 10, 4)
        clip_length = st.slider("Seconds per clip", 15, 90, 40, 5)
        model_size = st.selectbox("Local speech model", ["tiny", "base", "small"], index=1)
    with right:
        aspect = st.selectbox("Aspect ratio", ["9:16", "1:1", "16:9"])
        captions = st.checkbox("Burn speech captions", value=True)
        style = st.selectbox("Caption color", ["White", "Yellow"])
    rights = st.checkbox("I own or have permission to process this video.")
    submitted = st.form_submit_button("Generate local clips", type="primary")

if submitted:
    if not rights:
        st.error("Confirm that you have permission to process the video.")
    elif not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        st.error("FFmpeg and FFprobe are required. Install FFmpeg and restart this app.")
    else:
        try:
            with tempfile.TemporaryDirectory(prefix="localclip_") as folder:
                work = Path(folder)
                with st.spinner("Loading source video..."):
                    source = acquire_video(mode, url, local_path, uploaded, work)
                    duration = duration_of(source)
                with st.spinner(
                    "Transcribing locally (the first run downloads a free model; CPU can be slow)..."
                ):
                    segments = transcribe(source, model_size)
                choices = select_highlights(segments, duration, count, clip_length)
                if not choices:
                    raise RuntimeError("No clips could be selected.")
                if not segments:
                    st.warning("No speech found: clips are spaced across the video, without captions.")
                zip_bytes = render_clips(
                    source, work, segments, choices, aspect, captions, style
                )
                st.session_state["clip_zip"] = zip_bytes
                st.session_state["clip_results"] = choices
                st.success(f"Created {len(choices)} clips. Files stay on your PC.")
        except Exception as exc:
            st.error(f"Could not generate clips: {exc}")

if "clip_zip" in st.session_state:
    st.download_button(
        "Download clips (.zip)",
        data=st.session_state["clip_zip"],
        file_name="localclip_results.zip",
        mime="application/zip",
        type="primary",
    )
    st.dataframe(st.session_state["clip_results"], use_container_width=True)
