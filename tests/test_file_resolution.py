import tempfile
import unittest
from pathlib import Path

from scripts import media_converter as mc


class TestFileResolution(unittest.TestCase):
    def test_find_converted_file_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            original = base / "IMG_1000.HEIC"
            converted = base / "IMG_1000.JPG"
            original.write_bytes(b"a")
            converted.write_bytes(b"b")

            found = mc.find_converted_file(original, [".jpg"])
            self.assertEqual(found, converted)

    def test_find_original_converted_output_with_converted_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            original = base / "VID_2000.mp4"
            converted = base / "VID_2000_converted.mp4"
            original.write_bytes(b"source")
            converted.write_bytes(b"output")

            found = mc.find_original_converted_output(original, [".mp4"], db=None)
            self.assertEqual(found, converted)


if __name__ == "__main__":
    unittest.main()
