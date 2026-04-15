import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import media_converter as mc


class TestMainCLIFlow(unittest.TestCase):
    def test_only_images_and_only_videos_are_mutually_exclusive(self):
        with patch("sys.argv", ["media_converter.py", "--only-images", "--only-videos"]):
            with self.assertRaises(SystemExit) as ctx:
                mc.main()
        self.assertNotEqual(ctx.exception.code, 0)

    def test_main_exits_when_no_supported_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "note.txt").write_text("x", encoding="utf-8")

            with patch("sys.argv", ["media_converter.py", str(base)]), \
                 patch.object(mc, "check_dependencies", return_value=True), \
                 patch.object(mc, "check_hardware_acceleration", return_value="none"), \
                 patch.object(mc, "count_files", return_value={"heic": 0, "heif": 0, "hevc": 0, "aae": 12}), \
                 patch.object(mc, "process_directory") as process_mock, \
                 patch.object(mc, "log_message"):
                rc = mc.main()

            self.assertEqual(rc, 0)
            process_mock.assert_not_called()

    def test_remove_aae_is_skipped_in_videos_only_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "clip.MP4").write_bytes(b"x")
            (base / "meta.AAE").write_text("meta", encoding="utf-8")

            stats = {
                "images_converted": 0,
                "videos_converted": 0,
                "images_failed": 0,
                "videos_failed": 0,
                "images_skipped": 0,
                "videos_skipped": 0,
            }

            with patch("sys.argv", ["media_converter.py", str(base), "--only-videos", "--remove-aae"]), \
                 patch.object(mc, "check_dependencies", return_value=True), \
                 patch.object(mc, "check_hardware_acceleration", return_value="none"), \
                 patch.object(mc, "count_files", return_value={"heic": 0, "heif": 0, "hevc": 1}), \
                 patch.object(mc, "process_directory", return_value=(stats, [], [])), \
                 patch.object(mc, "_get_conversion_db", return_value=None), \
                 patch.object(mc, "remove_aae_files") as remove_aae_mock, \
                 patch.object(mc, "_handle_delete_originals"), \
                 patch.object(mc, "log_message"), \
                 patch("builtins.input", side_effect=["YES"]):
                rc = mc.main()

            self.assertEqual(rc, 0)
            remove_aae_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
