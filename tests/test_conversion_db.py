import tempfile
import unittest
from pathlib import Path

from scripts.conversion_db import ConversionDatabase


class TestConversionDatabase(unittest.TestCase):
    def test_record_and_find_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            db = ConversionDatabase(base / "data" / "conversion_db.json")

            original = base / "IMG_0001.HEIC"
            output = base / "IMG_0001.jpg"
            original.write_bytes(b"original")
            output.write_bytes(b"converted")

            db.record_conversion(
                original,
                output,
                file_type="image",
                image_format="JPEG",
            )

            found = db.find_output_path(original)
            self.assertEqual(found, output)
            self.assertTrue(db.is_converted(original))

    def test_record_conversion_deduplicates_same_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            db = ConversionDatabase(base / "data" / "conversion_db.json")

            original = base / "VID_0001.MOV"
            output = base / "VID_0001.mp4"
            original.write_bytes(b"a")
            output.write_bytes(b"b")

            db.record_conversion(original, output, file_type="video", codec="h264")
            db.record_conversion(original, output, file_type="video", codec="h264")

            records = db.all_records()
            self.assertEqual(len(records), 1)

    def test_find_output_path_returns_none_for_missing_or_empty_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            db = ConversionDatabase(base / "data" / "conversion_db.json")

            original = base / "VID_0002.MOV"
            output = base / "VID_0002.mp4"
            original.write_bytes(b"source")

            db.record_conversion(original, output, file_type="video", codec="h264")
            self.assertIsNone(db.find_output_path(original))

            output.write_bytes(b"")
            self.assertIsNone(db.find_output_path(original))


if __name__ == "__main__":
    unittest.main()
