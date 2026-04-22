import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import media_converter as mc


class TestMediaConverterProcessing(unittest.TestCase):
    def test_convert_video_safety_blocks_non_hevc(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "clip.mp4"
            input_file.write_bytes(b"x")

            fake_info = {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                    }
                ],
                "format": {"duration": "10"},
            }

            with patch.object(mc, "get_video_info", return_value=fake_info), patch.object(mc, "log_message"):
                success, output = mc.convert_video(input_file)

            self.assertFalse(success)
            self.assertEqual(output, input_file)

    def test_process_directory_converts_only_hevc_videos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            hevc_file = base / "A.MOV"
            h264_file = base / "B.MP4"
            hevc_file.write_bytes(b"1")
            h264_file.write_bytes(b"2")

            def fake_video_info(path: Path):
                codec = "hevc" if path.name == "A.MOV" else "h264"
                return {
                    "streams": [{"codec_type": "video", "codec_name": codec, "width": 1920, "height": 1080}],
                    "format": {"duration": "3"},
                }

            with patch.object(mc, "get_video_info", side_effect=fake_video_info), \
                 patch.object(mc, "find_recorded_converted_file", return_value=None), \
                 patch.object(mc, "find_converted_file", return_value=None), \
                 patch.object(mc, "_get_conversion_db", return_value=None), \
                 patch.object(mc, "convert_video", return_value=(True, base / "A.mp4")) as convert_mock, \
                 patch.object(mc, "log_message"):
                stats, converted, already = mc.process_directory(base, only_videos=True)

            self.assertEqual(stats["videos_converted"], 1)
            self.assertEqual(stats["videos_skipped"], 1)
            self.assertEqual(stats["videos_failed"], 0)
            self.assertEqual(len(converted), 1)
            self.assertEqual(len(already), 0)
            self.assertEqual(convert_mock.call_count, 1)
            self.assertIn("A.MOV", str(convert_mock.call_args[0][0]))

    def test_count_files_only_counts_hevc_videos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "x.mov").write_bytes(b"a")
            (base / "y.mp4").write_bytes(b"b")
            (base / "z.heic").write_bytes(b"c")

            def fake_video_info(path: Path):
                codec = "hevc" if path.name == "x.mov" else "h264"
                return {"streams": [{"codec_type": "video", "codec_name": codec}]}

            with patch.object(mc, "get_video_info", side_effect=fake_video_info), \
                 patch.object(mc, "_get_conversion_db", return_value=None), \
                 patch.object(mc, "find_recorded_converted_file", return_value=None), \
                 patch.object(mc, "find_converted_file", return_value=None):
                counts = mc.count_files(base)

            self.assertEqual(counts["hevc"], 1)
            self.assertEqual(counts["heic"], 1)

    def test_detect_hdr_returns_true_for_bt2020_smpte2084(self):
        """HDR should be detected when color_primaries=bt2020 and transfer=smpte2084"""
        fake_info = {
            "streams": [{
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 3840,
                "height": 2160,
                "pix_fmt": "yuv420p10le",
                "color_primaries": "bt2020",
                "transfer_characteristics": "smpte2084",
            }],
            "format": {"duration": "10"},
        }
        result = mc._is_hdr_video(fake_info)
        self.assertTrue(result)

    def test_detect_hdr_returns_false_for_bt709(self):
        """SDR should not be flagged as HDR"""
        fake_info = {
            "streams": [{
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 1920,
                "height": 1080,
                "pix_fmt": "yuv420p",
                "color_primaries": "bt709",
                "transfer_characteristics": "bt709",
            }],
            "format": {"duration": "10"},
        }
        result = mc._is_hdr_video(fake_info)
        self.assertFalse(result)

    def test_detect_hdr_returns_true_for_hlg(self):
        """HLG is also HDR"""
        fake_info = {
            "streams": [{
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 3840,
                "height": 2160,
                "pix_fmt": "yuv420p10le",
                "color_primaries": "bt2020",
                "transfer_characteristics": "arib-std-b67",
            }],
            "format": {"duration": "10"},
        }
        result = mc._is_hdr_video(fake_info)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
