# LocalClip — zero-subscription video clipper for Windows

A free, original **local starter app** for turning longer videos into short clips without Docker, paid APIs or video uploads to a hosted processing service.

## Features

- Paste a video URL (yt-dlp supported sites), select a local video path, or upload MP4/MOV/WebM/MKV/M4V.
- Generate multiple clips from speech-heavy moments, chosen with transparent heuristic scoring.
- Offline transcription via the free faster-whisper model (after its first model download).
- Burn phrase-level subtitles into 9:16, 1:1, or 16:9 clips with FFmpeg.
- Batch-download clips in one ZIP file with start/end/score metadata.
- Runs on a Windows PC with ~8 GB RAM; CPU-first for easy setup, NVIDIA GPU not required.

**Not yet implemented:** true AI virality prediction, face tracking/smart subject reframing, word-by-word animated captions, translation/dubbing, manual timeline editing, social-media publishing/scheduling, multi-account management, public share links or 100% ScaleReach.ai feature parity. Heuristic clip scores are **not** predictions of actual virality.

## Install on Windows (PowerShell)

1. Install **Python 3.11** from https://www.python.org/downloads/ (enable "Add Python to PATH").
2. Install FFmpeg, including FFprobe, with: `winget install --id Gyan.FFmpeg -e` (or download from https://ffmpeg.org/).
3. Restart PowerShell and verify `ffmpeg -version` and `ffprobe -version`.
4. Download this folder, open PowerShell inside it, and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501 if your browser did not open automatically.

For large videos, select **Local file path** instead of uploading into the browser. The first transcription run downloads a Whisper model to your machine; subsequent runs reuse the cache. Processing is free but can be slow on CPU, especially for hour-long videos. Set model to **tiny** for fastest results; **base** is the default compromise.

## Requirements

- Windows 10/11, Python 3.11, FFmpeg and FFprobe in PATH.
- 8 GB RAM recommended; enough free disk space for source, temporary clips and model cache.
- Internet only for installing packages, first model download, and URL downloads. Local-video processing itself does not call a paid AI API.
- Some platforms may restrict downloads; only process videos you own or have permission to use.

## What is published here?

This is an **independent MVP**, not a fork or redistribution of ScaleReach.ai proprietary code or of the OpenShorts project. The upstream OpenShorts project is here: https://github.com/mutonby/openshorts . Its full self-hosted feature set has separate infrastructure/GPU/API considerations.

No account credentials or API keys are needed for this app. Temporary working files are cleaned up after clip creation, while generated ZIP bytes remain in the running Streamlit session until that session ends.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## License

MIT (see LICENSE).