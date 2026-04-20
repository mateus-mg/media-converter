# Universal HEIC & HEVC Converter

Converts HEIC/HEIF images to JPEG 95% (or PNG) and MOV/MP4 videos with H.265/HEVC codec to H.264 (maximum compatibility). Compatible with files from iOS, GoPro, DJI, Samsung, Sony, and other devices.

**Only videos with H.265/HEVC codec are converted; videos already in H.264 or other codecs are skipped.**

> **Documentation:** Full documentation is now available at [https://mateus-mg.github.io/media-converter](https://mateus-mg.github.io/media-converter)

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Options Reference](#available-options)
- [Interactive Menu](#interactive-menu)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Safety](#safety)
- [Troubleshooting](#troubleshooting)

## Installation

### 1. System Dependencies (Required)

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg imagemagick

# Fedora/RHEL
sudo dnf install ffmpeg ImageMagick

# macOS (Homebrew)
brew install ffmpeg imagemagick
```

### 2. Python Environment (Recommended for Best Quality)

```bash
# Clone/Copy the script to your preferred location
cd /path/to/script

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install pillow pillow-heif
```

### 3. Install Global Command (Optional)

```bash
./media_converter.py --install
source ~/.bashrc  # Or restart terminal

# Now use converter from anywhere!
```

## Quick Start

```bash
# Basic conversion (interactive mode)
converter

# Convert specific folder with default settings
converter /path/to/photos

# Convert and delete originals (CAUTION!)
converter /path/to/photos --delete-originals
```

## Usage Examples

### Image Conversion

```bash
# HEIC → JPEG 95% (default - best quality/size balance)
converter /path/to/photos --image-format JPEG

# HEIC → PNG (lossless - larger files)
converter /path/to/photos --image-format PNG

# Only convert images (skip videos)
converter /path/to/photos --only-images

# Convert and remove Apple .AAE metadata files
converter /path/to/photos --remove-aae
```

### Video Conversion

```bash
# Convert only videos with H.265/HEVC codec to H.264
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

# Only convert videos (skip images)
converter /path/to/videos --only-videos
```

### Combined Operations

```bash
# Convert everything with optimal settings
converter /path/to/media --image-format JPEG --video-codec h264 --video-quality high

# Convert 4K videos to 1080p, images to JPEG, delete originals
converter /path/to/media --resize 1080p --image-format JPEG --delete-originals

# Dry run (simulate without converting)
converter /path/to/media --dry-run
```

## Interactive Menu

Run without arguments for an interactive menu:

```bash
converter
```

The interactive menu provides:
```
1. Convert images (HEIC/HEIF)
2. Convert videos (HEVC/H.265)
3. Convert images and videos (batch)
4. Remove AAE files
5. View system status
6. View conversion logs
7. Check dependencies
8. View hardware acceleration
9. Exit
```

## Available Options

### Image Options

| Option | Default | Description |
|--------|---------|-------------|
| `--image-format FORMAT` | JPEG | Output format: JPEG (95% quality) or PNG (lossless) |
| `--only-images` | false | Process only images (skip videos) |

### Video Options

| Option | Default | Description |
|--------|---------|-------------|
| `--video-codec CODEC` | h264 | Codec: h264 (maximum compatibility), h265 (efficient), copy (remux) |
| `--video-quality QUALITY` | high | Quality: lossless, high (CRF 18-23), medium (CRF 23) |
| `--resize RESOLUTION` | none | Resize: 4k (keep), 2k/1440p, 1080p, none |
| `--only-videos` | false | Process only videos (skip images) |

### Processing Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | false | Simulate conversion without processing |
| `--delete-originals` | false | **CAUTION**: Delete originals after successful conversion |
| `--remove-aae` | false | Remove Apple .AAE editing metadata files |
| `--install` | false | Install 'converter' command globally |

## Features

### Image Conversion

- ✅ Converts only HEIC/HEIF images to JPEG/PNG (other formats are skipped)
- ✅ Pillow (preferred): Maximum quality with pillow-heif backend
- ✅ ImageMagick (fallback): Automatic fallback if Pillow unavailable
- ✅ EXIF preservation: Maintains orientation and metadata
- ✅ Smart compression: JPEG 95% or PNG lossless compression level 9
- ✅ Color space conversion: Automatic RGB conversion when needed

### Video Conversion

- ✅ Converts only MOV/MP4 videos with H.265/HEVC codec to H.264
- ✅ Hardware acceleration: Auto-detects NVIDIA NVENC, Intel QSV, Software (dynamic detection)
- ✅ 10-bit support: Uses High 10 Profile for 10-bit sources (software encoder)
- ✅ DOVI (Dolby Vision) support: Auto-detects and handles DOVI content (uses NVENC or software)
- ✅ Bitrate-aware quality: Auto CRF based on source bitrate: <10Mbps→18-19, 10-25Mbps→20-21, 25-50Mbps→22-23, >50Mbps→23-24
- ✅ Smart resizing: Never upscales, maintains aspect ratio
- ✅ Faststart: Enables web streaming compatibility
- ✅ Metadata preservation: Copies creation/modification dates
- ✅ Output validation: Verifies codec, resolution and duration after conversion
- ✅ Optional audio handling: Videos without audio are processed correctly
- ✅ Output file: If input is already .mp4, output will be named with _converted suffix to avoid overwriting

### Preset & Quality Logic

- ✅ Preset is chosen automatically based on hardware, resolution, aspect ratio and codec
- ✅ CRF is set automatically by source bitrate (see Technical Details)
- ✅ 10-bit sources force software encoder to preserve quality (NVENC/QSV limitations)

### File Counting & Safety

- ✅ Only files that actually need conversion are counted and processed
- ✅ No overwrites: Skips existing converted files
- ✅ Success verification: Only deletes originals after successful conversion
- ✅ Confirmation prompts: Requires 'YES' for destructive operations
- ✅ Error isolation: Failed conversions preserve originals
- ✅ Dry run mode: Preview actions without changes

## System Architecture

The system is composed of the following modules:

| Module | Description |
|--------|-------------|
| `media_converter.py` | Core conversion logic for images and videos |
| `cli_manager.py` | Interactive CLI menu interface |
| `conversion_db.py` | JSON database for tracking converted files (deduplication) |
| `config.py` | Configuration management from `.env` file |
| `interactive_helpers.py` | Shared prompt helpers for interactive mode |
| `log_config.py` | Logging configuration and log functions |
| `log_formatter.py` | Structured log formatting (sections, headers, progress) |

### Conversion Database

The system maintains a conversion history database (`data/conversion_db.json`) to:
- Track successfully converted files
- Prevent duplicate conversions
- Enable smart skipping of already-converted files

## Safety

### Before Deleting Originals

1. Always test first: Use `--dry-run` to preview actions
2. Verify conversions: Check converted files before deleting
3. Backup important data: Keep backups of irreplaceable media
4. Use confirmation: Script requires 'YES' for deletion

### Safe Usage Pattern

```bash
# Step 1: Dry run to see what will happen
converter /path/to/photos --dry-run --delete-originals

# Step 2: Convert without deletion
converter /path/to/photos

# Step 3: Verify converted files are correct

# Step 4: Delete originals (if confident)
converter /path/to/photos --delete-originals
```

## Troubleshooting

### Common Issues

**"Missing dependencies" error**

```bash
# Verify installations
ffmpeg -version
convert --version  # or magick --version
```

**Hardware acceleration not detected**

```bash
# Check available encoders
ffmpeg -hide_banner -encoders | grep -E "(qsv|nvenc|vaapi)"

# Intel QSV drivers (Ubuntu)
sudo apt install intel-media-va-driver-non-free i965-va-driver

# Test hardware encoding
ffmpeg -hide_banner -f lavfi -i nullsrc=s=256x256:d=1 -c:v h264_qsv -f null -
```

**HEIC conversion fails with Pillow**

```bash
# Install required packages
pip install --upgrade pillow pillow-heif

# Or use ImageMagick fallback (auto-detected)
```

**Video file size increased after conversion**

- Expected: HEVC → H.264 typically increases size by ~30-50%
- HEVC is 50% more efficient than H.264
- Solution: Use `--video-codec h265` to maintain HEVC encoding

### Performance Tips

**For faster 4K conversion:**

```bash
converter /path/4k --resize 2k --video-quality medium
# 3-4x faster with minimal quality loss
```

**For maximum quality:**

```bash
converter /path/media --image-format PNG --video-quality high --resize 4k
```

**For compatibility (social media, older devices):**

```bash
converter /path/media --image-format JPEG --video-codec h264 --resize 1080p
```

## Technical Details

### Conversion Pipeline

**HEIC/HEIF Images:**
- Primary: Pillow + pillow-heif → JPEG/PNG
- Fallback: ImageMagick → JPEG/PNG

**H.265/HEVC Videos:**
- Dynamic hardware detection → NVIDIA NVENC > Intel QSV > Software
- 10-bit sources force Software encoder (High 10 Profile)
- DOVI (Dolby Vision) detected: uses NVENC if available, else software
- Detect codec via ffprobe (not by extension)
- Only MOV/MP4 with H.265/HEVC are converted
- Auto CRF based on source bitrate, preset based on hardware type
- Output validation: verifies codec, resolution, duration after conversion
- Videos without audio are processed correctly (no audio codec error)
- Output file: If input is .mp4, output will be named with _converted suffix
- H.264 output for maximum compatibility

### Quality Settings Explained

- **JPEG 95%**: Optimal quality/size balance, visually lossless
- **PNG**: True lossless, uses maximum compression (level 9)

### Video CRF (by source bitrate):

| Bitrate | CRF | Use Case |
|---------|-----|----------|
| <10 Mbps | 18-19 | Preserve details in low bitrate sources |
| 10-25 Mbps | 20-21 | Balanced |
| 25-50 Mbps | 22-23 | Control size for high bitrate |
| >50 Mbps | 23-24 | Prioritize size control |

### Hardware Acceleration Priority

- **NVIDIA NVENC**: Fast, `-cq` parameter (best performance, not all GPUs support 10-bit)
- **Intel Quick Sync (QSV)**: Fast, `-global_quality` parameter
- **Software (libx264)**: CPU-based, compatible everywhere (required for 10-bit sources)

Note: 10-bit H264 sources force Software encoder (NVENC/QSV limitations)

## Virtual Environment Management

**Manual activation:**

```bash
source venv/bin/activate  # Linux/macOS
./media_converter.py /path/to/media
deactivate
```

**Automatic (with global command):**

```bash
converter /path/to/media  # Auto-activates/deactivates venv
```

**Global command troubleshooting:**

```bash
# Reinstall global command
./media_converter.py --install
exec $SHELL  # Reload shell configuration

# Check alias
type converter
```

## License & Attribution

This tool combines:

- FFmpeg for video processing
- ImageMagick/Pillow for image conversion
- Python standard libraries

Always respect copyright and personal media rights. Use responsibly.
