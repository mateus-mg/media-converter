import unittest
from unittest.mock import patch

from scripts.interactive_helpers import build_conversion_config


class TestInteractiveHelpers(unittest.TestCase):
    def test_required_questions_are_asked_when_not_customizing(self):
        # Flow: customize? no -> required delete originals -> required remove aae
        answers = iter(["n", "y", "n"])

        def fake_input(_prompt: str) -> str:
            return next(answers)

        config = build_conversion_config(preselected_mode=None, input_func=fake_input)

        self.assertTrue(config["delete_originals"])
        self.assertFalse(config["remove_aae"])
        self.assertFalse(config["only_videos"])

    def test_remove_aae_not_asked_in_videos_only_when_not_customizing(self):
        prompts = []
        answers = iter(["n", "y"])  # customize=no, delete originals=yes

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            return next(answers)

        config = build_conversion_config(preselected_mode="videos", input_func=fake_input)

        self.assertTrue(config["only_videos"])
        self.assertTrue(config["delete_originals"])
        self.assertFalse(config["remove_aae"])
        self.assertFalse(any(".AAE" in p for p in prompts))

    def test_remove_aae_not_asked_in_videos_only_when_customizing(self):
        # customize=yes, choose videos-only, choose codec/quality/resize, dry_run, delete originals
        answers = iter(["y", "3", "1", "1", "1", "n", "n"])
        prompts = []

        def fake_input(prompt: str) -> str:
            prompts.append(prompt)
            return next(answers)

        config = build_conversion_config(preselected_mode=None, input_func=fake_input)

        self.assertTrue(config["only_videos"])
        self.assertFalse(any(".AAE" in p for p in prompts))


if __name__ == "__main__":
    unittest.main()
