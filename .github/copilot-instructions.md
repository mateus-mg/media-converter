# Media Converter - Developer Guide

## Core Rules

### 1. Language & Documentation Rule
**All code, comments, documentation, and user-facing text MUST be in English.**
- After any upgrade or feature addition, update both:
  1. `README.md` - User documentation
  2. `copilot-instructions.md` - Developer documentation
- Confirm prompts use uppercase 'YES' (not 'SIM' or other languages)

### 2. Image Conversion Priority

HEIC/HEIF → Pillow (if available) → JPEG 95% OR PNG
↓
ImageMagick (fallback) → JPEG OR PNG
text


**Pillow path:** `convert_image_pillow()` → `Image.open()` → `exif_transpose()` → `save()`
**IM path:** `convert_image_imagemagick()` → `magick/convert` command

### 3. Video Encoding Pipeline

MOV/MP4 → detect resolution → choose CRF → select encoder → encode
↓
Hardware detection: QSV > NVENC > VAAPI > libx264
text


**CRF logic:**
- 4K (≥2160p): CRF 23
- 2K (≥1440p): CRF 20  
- 1080p or less: CRF 18

### 4. File Safety Rules
- Never overwrite existing converted files
- Only delete originals after successful conversion AND user confirmation
- Preserve original timestamps with `os.utime()`
- Skip files with `_converted` in name

## Code Structure

### Main Functions
```python
main()  # Entry point
├── check_dependencies()  # Verify ffmpeg, imagemagick
├── check_hardware_acceleration()  # Detect QSV/NVENC/VAAPI
├── count_files()  # Count ONLY files to be converted (excludes already converted)
├── process_directory()  # Process all files
│   ├── convert_image()  # Images
│   └── convert_video()  # Videos
└── install_command()  # Global installer

Key Functions Location

    convert_image(): Lines 230-260

    convert_video(): Lines 320-460

    process_directory(): Lines 550-690

    count_files(): Lines 135-200 (smart counter - excludes already converted)

    Hardware detection: Lines 110-140

    Deletion logic: Lines 1040-1100 (handles both new and already converted files)

Important Corrections Applied
Fixed Default Values

    Image format: Parser shows PNG as default, but code forces JPEG as actual default

    Video codec: Parser shows h265 as default, but code forces h264 as actual default

    Python packages: Added check_python_packages() function to warn about missing Pillow

Safety Improvements

    Deletion logic: Shows BOTH newly converted files AND already converted files for deletion

    User choice: User can delete originals from both current run and previous runs

    Verification: Checks if converted file exists and has valid size before deleting original

    Confirmation: Clear separation between newly converted and already converted files

    Smart counters: Only counts files that will actually be converted (excludes already converted)

Adding New Features
1. New Image Format
python

# 1. Add to argparse (line ~468)
parser.add_argument('--image-format', choices=['PNG','JPEG','NEWFORMAT'])

# 2. Update convert_image_pillow() and convert_image_imagemagick()
# 3. Add file extension mapping in convert_image_pillow() line ~245
# 4. Update both documentation files (English only)

2. New Video Codec
python

# 1. Add to argparse choices (line ~474)
# 2. Update convert_video() lines 380-410
# 3. Add encoder parameters in lines 415-450
# 4. Update documentation examples

3. New File Type
python

# 1. Add to count_files() dictionary (line 155)
# 2. Add to image_extensions or video_extensions in process_directory()
# 3. Add conversion function
# 4. Document supported formats in README

FFmpeg Parameters by Encoder
Intel QSV
python

['-c:v', 'h264_qsv', '-global_quality', crf, '-preset', 'medium']

NVIDIA NVENC
python

['-c:v', 'h264_nvenc', '-cq', crf, '-preset', 'p4']

Software (libx264)
python

['-c:v', 'libx264', '-crf', crf, '-preset', 'medium']

Common to all:
python

['-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart']

Testing Commands
Test Hardware Encoding
bash

# Quick test
ffmpeg -f lavfi -i nullsrc=s=256x256:d=1 -c:v h264_qsv -f null -

# List available
ffmpeg -encoders | grep -E "(qsv|nvenc|vaapi)"

Test Image Conversion
python

python3 -c "
from pathlib import Path
success, path = convert_image(Path('test.heic'), use_png=False)
print(f'Success: {success}, Output: {path}')
"

Dry Run
bash

./media_converter.py /path --dry-run --only-images

Documentation Update Checklist

After ANY code change:

    Update README.md options/descriptions/examples

    Update copilot-instructions.md technical details

    Verify all text is in English

    Test examples in documentation work

    Check confirmation prompts use 'YES'

Debug Checklist
Images Not Converting

    Check Pillow: python3 -c "import PIL; print(PIL.__version__)"

    Check fallback: which magick or which convert

    Test manually: convert input.heic output.jpg

Videos Slow

    Check hardware: ./media_converter.py (shows detected acceleration)

    Reduce quality: Use --video-quality medium

    Downscale: Use --resize 1080p

Deletion Issues

    Check permissions: ls -la /path/to/file

    Check if file exists: Script verifies before deleting

    Confirm uppercase 'YES' required

Maintenance Tips
1. Keep Dependencies Updated
bash

# In virtual environment
pip install --upgrade pillow pillow-heif

2. Test Hardware Changes
bash

# After driver updates
sudo apt update intel-media-va-driver-non-free
./media_converter.py --dry-run  # Shows detected hardware

3. Monitor Performance
bash

# During conversion
htop  # CPU usage
nvidia-smi  # GPU usage (NVIDIA)

4. Safe Updates Workflow
bash

# 1. Make code changes (English only)
# 2. Test with --dry-run
# 3. Update both documentation files
# 4. Verify all examples work
# 5. Commit with clear English messages

Quick Reference

Language Rule: English only for code and docs
Update Rule: Docs updated after any change
Defaults: JPEG images, H.264 videos, high quality
Hardware: Auto-detects, falls back to software
Safety: No overwrites, confirmations for deletion
Structure: Main → Process → Convert (Image/Video)
Testing: Dry-run first, verify outputs, then delete
Critical Fixes Summary

    Default image format: Code forces JPEG as default despite parser saying PNG

    Default video codec: Code forces h264 as default despite parser saying h265

    Python package check: Added warning system for missing Pillow

4. **Deletion safety**: Shows BOTH newly converted AND already converted files, user can choose to delete originals from both lists

5. **File counting**: Smart counter that only counts files to be converted, excludes already converted files

6. **Verification**: Before deleting any original, verifies converted file exists and has valid size