from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from yt_auto.pixel_effects import apply_effects, apply_video_effects, infer_effects


class PixelEffectsTests(unittest.TestCase):
    def test_story_tags_are_inferred(self):
        tags = infer_effects("The freezing ocean waves struck the iceberg.")
        self.assertTrue({"snow", "ice_shimmer", "water", "impact"}.issubset(tags))

    def test_effects_are_deterministic_and_change_rgb_pixels(self):
        frame = np.zeros((120, 80, 3), dtype=np.uint8)
        first = apply_effects(frame, 0.4, ["snow", "ice_shimmer", "water"], seed=7)
        second = apply_effects(frame, 0.4, ["snow", "ice_shimmer", "water"], seed=7)
        self.assertEqual(first.shape, frame.shape)
        self.assertTrue(np.array_equal(first, second))
        self.assertTrue(np.any(first != frame))

    def test_lantern_adds_warm_light(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = apply_effects(frame, 0.2, ["lantern"])
        self.assertGreater(int(result[..., 0].sum()), int(result[..., 1].sum()))

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is not installed")
    def test_effects_process_a_video_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.mp4"
            output = Path(tmp) / "output.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                "color=c=black:s=80x120:r=10:d=1", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", str(source),
            ], check=True)
            apply_video_effects(source, output, ["snow", "ice_shimmer", "water"],
                                width=80, height=120, fps=10, seed=3)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
