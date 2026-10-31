import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from yt_auto.binary_scene import load_plan, render_frame, render_video


class BinarySceneTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "duration": 2,
            "objects": [
                {"id": "ground", "type": "rect", "x": 0, "y": 0.8, "w": 1, "h": 0.2},
                {"id": "moving-car", "type": "rect", "x": 0.1, "y": 0.5, "w": 0.2, "h": 0.1,
                 "motion": {"start": 0, "end": 2, "dx": 0.5, "dy": 0}},
            ],
        }

    def test_frame_is_strictly_binary(self):
        frame = render_frame(self.plan, 0.5, 160, 284)
        self.assertEqual(set(np.unique(frame).tolist()), {0, 255})
        self.assertEqual(frame.shape, (284, 160))

    def test_motion_changes_pixel_pattern(self):
        first = render_frame(self.plan, 0.1, 160, 284)
        later = render_frame(self.plan, 1.8, 160, 284)
        self.assertFalse(np.array_equal(first, later))

    def test_rejects_unknown_shape(self):
        with self.assertRaises(ValueError):
            render_frame({"duration": 1, "objects": [{"id": "bad", "type": "photo"}]}, 0)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for video integration test")
    def test_video_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.mp4"
            report = render_video(self.plan, path, width=160, height=284, fps=4)
            self.assertTrue(path.exists())
            self.assertEqual(report["frames"], 8)
            self.assertEqual(report["pixel_states"], [0, 255])
            self.assertEqual(report["source_images_used"], 0)
            self.assertEqual(report["source_video_used"], 0)


if __name__ == "__main__":
    unittest.main()
