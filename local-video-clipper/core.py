"""Offline clip selection, captions, and video layout helpers."""
from __future__ import annotations

import re
from pathlib import Path

HOOK_WORDS = (
    "why", "how", "secret", "mistake", "never", "always", "biggest",
    "best", "worst", "important", "surprise", "imagine", "truth",
    "problem", "solution", "first", "finally", "million", "warning",
)


def select_highlights(segments: list[dict], duration: float, count: int, length: int) -> list[dict]:
    """Rank speech-dense windows using local, transparent heuristics.

    Scores are NOT estimates of social-media virality. Windows do not overlap.
    """
    duration = float(duration)
    if duration <= 0:
        raise ValueError("Video duration must be positive")
    length = min(duration, max(8.0, float(length)))
    max_start = max(0.0, duration - length)
    candidates = {round(max_start * i / 24, 2) for i in range(25)}
    candidates.update(round(min(max(float(s["start"]) - 2, 0), max_start), 2) for s in segments)

    scored = []
    for start in candidates:
        end = min(duration, start + length)
        relevant = [
            s for s in segments
            if float(s["end"]) > start and float(s["start"]) < end
        ]
        phrase = " ".join(str(s["text"]) for s in relevant).strip()
        tokens = re.findall(r"\b[\w']+\b", phrase.lower())
        matches = sum(1 for w in tokens if w in HOOK_WORDS)
        punctuation = phrase.count("?") + phrase.count("!")
        density = min(len(tokens) / max(1, length), 3.5)
        score = round(density * 20 + matches * 7 + punctuation * 3, 1)
        scored.append({"start":start, "end":end, "score":score, "text":phrase[:220]})

    picked: list[dict] = []
    for item in sorted(scored, key=lambda c: (-c["score"], c["start"])):
        if all(
            min(item["end"], other["end"]) - max(item["start"], other["start"]) <= 0
            for other in picked
        ):
            picked.append(item)
        if len(picked) >= count:
            break

    return sorted(picked, key=lambda c: c["start"])


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def write_srt(segments: list[dict], start: float, end: float, path: Path) -> int:
    """Write relative-timed phrase subtitles for a selected source window."""
    entries = []
    for segment in segments:
        a = max(float(segment["start"]), start)
        b = min(float(segment["end"]), end)
        text = re.sub(r"\s+", " ", str(segment["text"])).strip()
        if b - a >= 0.1 and text:
            text = text.replace("-->", "→")
            entries.append(
                f"{len(entries) + 1}\n{_timestamp(a - start)} --> {_timestamp(b - start)}\n{text}\n"
            )
    path.write_text("\n".join(entries), encoding="utf-8")
    return len(entries)


def video_filter(aspect: str, srt: str | None = None, style: str = "White") -> str:
    dimensions = {"9:16": (720, 1280), "1:1": (720, 720), "16:9": (1280, 720)}
    if aspect not in dimensions:
        raise ValueError(f"Unsupported aspect ratio: {aspect}")
    width, height = dimensions[aspect]
    filters = [
        f"scale={width}:{height}:force_original_aspect_ratio=increase",
        f"crop={width}:{height}",
        "setsar=1",
    ]
    if srt:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.srt", srt):
            raise ValueError("Unsafe subtitle filename")
        color = "&H0000FFFF" if style == "Yellow" else "&H00FFFFFF"
        settings = (
            f"FontName=Arial,FontSize=19,PrimaryColour={color},"
            "OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=65"
        )
        filters.append(f"subtitles={srt}:force_style='{settings}'")
    return ",".join(filters)
