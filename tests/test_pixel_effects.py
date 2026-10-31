from __future__ import annotations

import unittest

import numpy as np

from yt_auto.pixel_effects import apply_effects, infer_effects


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


if __name__ == "__main__":
    unittest.main()
