# Universal HEIC & HEVC Converter

Converts HEIC/HEIF images to JPEG 95% (or PNG) and MOV/MP4 videos with H.265/HEVC codec to H.264 (maximum compatibility). Compatible with files from iOS, GoPro, DJI, Samsung, Sony, and other devices. **Only videos with H.265/HEVC codec are converted; videos already in H.264 or other codecs are skipped.**

## 📋 Table of Contents
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Options Reference](#-available-options)
- [Features](#-features)
- [Safety](#-safety)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation

### 1. System Dependencies (Required)
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg imagemagick

# Fedora/RHEL
sudo dnf install ffmpeg ImageMagick

# macOS (Homebrew)
brew install ffmpeg imagemagick

2. Python Environment (Recommended for Best Quality)
bash

# Clone/Copy the script to your preferred location
cd /path/to/script

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install pillow pillow-heif

3. Install Global Command (Optional)
bash

./media_converter.py --install
source ~/.bashrc  # Or restart terminal

Now use converter from anywhere!
⚡ Quick Start
bash

# Basic conversion (interactive mode)
converter

# Convert specific folder with default settings
# (JPEG 95% for images, H.264 for videos with H.265/HEVC codec)
converter /path/to/photos

# Convert and delete originals (CAUTION!)
# Will show both newly converted and already converted files
converter /path/to/photos --delete-originals

📖 Usage Examples
Image Conversion
bash

# HEIC → JPEG 95% (default - best quality/size balance)
converter /path/to/photos --image-format JPEG

# HEIC → PNG (lossless - larger files)
converter /path/to/photos --image-format PNG

# Only convert images (skip videos)
converter /path/to/photos --only-images

# Convert and remove Apple .AAE metadata files
converter /path/to/photos --remove-aae

Video Conversion
bash

# Convert only videos with H.265/HEVC codec to H.264 (maximum compatibility)
converter /path/to/videos --video-codec h264

# Convert to H.265/HEVC (better compression)
converter /path/to/videos --video-codec h265

# Remux only (no re-encoding)
converter /path/to/videos --video-codec copy

# Resize 4K videos to 1440p (2K) for faster processing
converter /path/to/4k-videos --resize 2k

# High quality for 1080p or lower
converter /path/to/videos --video-quality high

# Medium quality (smaller files)
converter /path/to/videos --video-quality medium

# Lossless quality (very large files)
converter /path/to/videos --video-quality lossless

# Only convert HEVC/H.265 videos
converter /path/to/videos --only-hevc-videos

# Only convert videos (skip images)
converter /path/to/videos --only-videos

Combined Operations
bash

# Convert everything with optimal settings
converter /path/to/media --image-format JPEG --video-codec h264 --video-quality high

# Convert 4K videos to 1080p, images to JPEG, delete originals
converter /path/to/media --resize 1080p --image-format JPEG --delete-originals

# Dry run (simulate without converting)
converter /path/to/media --dry-run

⚙️ Available Options
Image Options
Option	Default	Description
--image-format FORMAT	JPEG	Output format: JPEG (95% quality) or PNG (lossless)
--only-images	false	Process only images (skip videos)
Video Options
Option	Default	Description
--video-codec CODEC	h264	Codec: h264 (maximum compatibility), h265 (efficient), copy (remux)
--video-quality QUALITY	high	Quality: lossless, high (CRF 18-23), medium (CRF 23)
--resize RESOLUTION	none	Resize: 4k (keep), 2k/1440p, 1080p, none
--only-videos	false	Process only videos (skip images)
--only-hevc-videos	false	Process only H.265/HEVC encoded videos
Processing Options
Option	Default	Description
--dry-run	false	Simulate conversion without processing
--delete-originals	false	CAUTION: Delete originals after successful conversion
--remove-aae	false	Remove Apple .AAE editing metadata files

🎯 Key Features
Image Conversion

    ✅ Converts only HEIC/HEIF images to JPEG/PNG (other formats are skipped)
    ✅ Pillow (preferred): Maximum quality with pillow-heif backend
    ✅ ImageMagick (fallback): Automatic fallback if Pillow unavailable
    ✅ EXIF preservation: Maintains orientation and metadata
    ✅ Smart compression: JPEG 95% or PNG lossless compression level 9
    ✅ Color space conversion: Automatic RGB conversion when needed

Video Conversion

    ✅ Converts only MOV/MP4 videos with H.265/HEVC codec to H.264 (other codecs are skipped)
    ✅ Hardware acceleration: Auto-detects Intel QSV, NVIDIA NVENC, VAAPI
    ✅ Resolution-aware quality: Auto CRF: 23(4K), 20(2K), 18(≤1080p)
    ✅ Smart resizing: Never upscales, maintains aspect ratio
    ✅ Faststart: Enables web streaming compatibility
    ✅ Metadata preservation: Copies creation/modification dates
    ✅ Output file: If input is already .mp4, output will be named with _converted suffix to avoid overwriting

Preset & Quality Logic

    ✅ Preset is chosen automatically based on hardware, resolution, aspect ratio and codec:
        - 16:9 videos use faster presets
        - Non-16:9 videos use slower presets for better quality
        - H.265 always uses slower presets for better compression
    ✅ CRF is set automatically by resolution (see above)

File Counting & Safety

    ✅ Only files that actually need conversion are counted and processed
    ✅ No overwrites: Skips existing converted files
    ✅ Success verification: Only deletes originals after successful conversion
    ✅ Confirmation prompts: Requires 'YES' for destructive operations
    ✅ Error isolation: Failed conversions preserve originals
    ✅ Dry run mode: Preview actions without changes

🛡️ Safety Guidelines

Before Deleting Originals

    Always test first: Use --dry-run to preview actions

    Verify conversions: Check converted files before deleting

    Backup important data: Keep backups of irreplaceable media

    Use confirmation: Script requires 'YES' for deletion

    Smart deletion: Script shows both newly converted files AND already converted files with originals still present

Safe Usage Pattern
bash

# Step 1: Dry run to see what will happen
converter /path/to/photos --dry-run --delete-originals

# Step 2: Convert without deletion
converter /path/to/photos

# Step 3: Verify converted files are correct

# Step 4: Delete originals (if confident)
# The script will show:
#  - Files converted in this run
#  - Files already converted (originals still present)
converter /path/to/photos --delete-originals

🔧 Technical Details
Conversion Pipeline
text

HEIC/HEIF Images:
    Primary: Pillow + pillow-heif → JPEG/PNG
    Fallback: ImageMagick → JPEG/PNG

H.265/HEVC Videos:
    Detect hardware → QSV > NVENC > VAAPI > Software
    Detect codec via ffprobe (not by extension)
    Only MOV/MP4 with H.265/HEVC are converted
    Auto CRF and preset based on resolution, aspect ratio, hardware
    Output file: If input is .mp4, output will be named with _converted suffix
    H.264 output for maximum compatibility

Quality Settings Explained

    JPEG 95%: Optimal quality/size balance, visually lossless

    PNG: True lossless, uses maximum compression (level 9)

    Video CRF: Lower = better quality, higher = smaller files

        CRF 18: Visually lossless (≤1080p)

        CRF 20: High quality (2K/1440p)

        CRF 23: Good quality, smaller files (4K)

Hardware Acceleration Priority

    Intel Quick Sync (QSV): Fastest, -global_quality parameter

    NVIDIA NVENC: Fast, -cq parameter

    VAAPI: Generic hardware acceleration

    Software (libx264): CPU-based, compatible everywhere

🐛 Troubleshooting
Common Issues

"Missing dependencies" error
bash

# Verify installations
ffmpeg -version
convert --version  # or magick --version

Hardware acceleration not detected
bash

# Check available encoders
ffmpeg -hide_banner -encoders | grep -E "(qsv|nvenc|vaapi)"

# Intel QSV drivers (Ubuntu)
sudo apt install intel-media-va-driver-non-free i965-va-driver

# Test hardware encoding
ffmpeg -hide_banner -f lavfi -i nullsrc=s=256x256:d=1 -c:v h264_qsv -f null -

HEIC conversion fails with Pillow
bash

# Install required packages
pip install --upgrade pillow pillow-heif

# Or use ImageMagick fallback (auto-detected)

Video file size increased after conversion

    Expected: HEVC → H.264 typically increases size by ~30-50%

    HEVC is 50% more efficient than H.264

    Solution: Use --video-codec h265 to maintain HEVC encoding

Performance Tips

For faster 4K conversion:
bash

converter /path/to/4k --resize 2k --video-quality medium
# 3-4x faster with minimal quality loss

For maximum quality:
bash

converter /path/to/media --image-format PNG --video-quality high --resize 4k

For compatibility (social media, older devices):
bash

converter /path/to/media --image-format JPEG --video-codec h264 --resize 1080p

📝 Virtual Environment Management

Manual activation:
bash

source venv/bin/activate  # Linux/macOS
./media_converter.py /path/to/media
deactivate

Automatic (with global command):
bash

converter /path/to/media  # Auto-activates/deactivates venv

Global command troubleshooting:
bash

# Reinstall global command
./media_converter.py --install
exec $SHELL  # Reload shell configuration

# Check alias
type converter

📄 License & Attribution

This tool combines:

    FFmpeg for video processing

    ImageMagick/Pillow for image conversion

    Python standard libraries

Always respect copyright and personal media rights. Use responsibly.