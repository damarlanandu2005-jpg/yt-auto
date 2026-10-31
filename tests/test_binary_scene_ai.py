import unittest
from unittest.mock import patch

from yt_auto.binary_scene_ai import plan_scene


class BinarySceneAITests(unittest.TestCase):
    @patch("yt_auto.binary_scene_ai.llm.llm")
    def test_requests_text_only_geometry_and_validates_result(self, mock_llm):
        mock_llm.return_value = {
            "duration": 3,
            "objects": [
                {"id": "body", "type": "rect", "x": 0.2, "y": 0.5, "w": 0.5, "h": 0.2},
                {"id": "wheel", "type": "ellipse", "x": 0.25, "y": 0.65, "w": 0.1, "h": 0.1},
            ],
        }
        plan = plan_scene("A small car drives along a road", "The car moves forward.", 3)
        self.assertEqual(plan["duration"], 3.0)
        self.assertEqual(len(plan["objects"]), 2)
        kwargs = mock_llm.call_args.kwargs
        self.assertNotIn("images", kwargs)
        self.assertEqual(kwargs["name"], "binary_scene_plan")

    @patch("yt_auto.binary_scene_ai.llm.llm")
    def test_rejects_out_of_bounds_geometry(self, mock_llm):
        mock_llm.return_value = {
            "duration": 2,
            "objects": [{"id": "bad", "type": "rect", "x": 1.2, "y": 0.2, "w": 0.1, "h": 0.1}],
        }
        with self.assertRaises(ValueError):
            plan_scene("A car", "A car drives.", 2)


if __name__ == "__main__":
    unittest.main()
