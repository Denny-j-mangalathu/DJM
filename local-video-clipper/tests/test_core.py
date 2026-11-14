import tempfile
import unittest
from pathlib import Path
from core import select_highlights, write_srt, video_filter


class CoreTests(unittest.TestCase):
    def test_selection_nonoverlap(self):
        segments = [
            {"start": t, "end": t + 2, "text": "Why is this important? Here is a solution!"}
            for t in range(0, 160, 5)
        ]
        clips = select_highlights(segments, 180, 3, 35)
        self.assertEqual(len(clips), 3)
        for a, b in zip(clips, clips[1:]):
            self.assertLessEqual(a["end"], b["start"])

    def test_no_speech_fallback(self):
        clips = select_highlights([], 120, 2, 30)
        self.assertEqual(len(clips), 2)

    def test_srt_time_relative(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.srt"
            count = write_srt(
                [{"start": 13.0, "end": 15.0, "text": "Hello world"}],
                10, 30, path,
            )
            self.assertEqual(count, 1)
            self.assertIn("00:00:03,000 --> 00:00:05,000", path.read_text())

    def test_video_filter(self):
        self.assertIn("crop=720:1280", video_filter("9:16"))
        self.assertIn("subtitles=captions_01.srt", video_filter("9:16", "captions_01.srt"))
        with self.assertRaises(ValueError):
            video_filter("9:16", "../unsafe.srt")


if __name__ == "__main__":
    unittest.main()
