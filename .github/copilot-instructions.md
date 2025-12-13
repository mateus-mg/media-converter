
# Copilot Instructions - Universal HEIC & HEVC Converter

## Project Overview
Python-based media conversion tool for mobile and camera photos/videos. Converts HEIC→JPEG 95%, MOV/MP4→H.264 with hardware acceleration (Intel Quick Sync/VAAPI). Located in the project root.

## Architecture

**Main Script:** `media_converter.py` (~1000 lines)
- Dual conversion paths: Pillow (preferred) → ImageMagick (fallback) for images
- Hardware-accelerated video encoding: QSV > NVENC > VAAPI > software fallback
- Auto-detects resolution and adjusts CRF: 4K→CRF23, 2K→CRF20, ≤1080p→CRF18

**Key Components:**
- `check_hardware_acceleration()`: Tests encoders (QSV/NVENC/VAAPI) with actual encoding attempts
- `convert_image()`: HEIC→JPEG 95% with Lanczos filter, compression-level 9
- `convert_video()`: H.264 encoding with resolution-aware quality settings
- `process_directory()`: Recursive file discovery, respects existing outputs

## Critical Patterns

**Video Quality Logic (Lines 380-410):**
```python
# Auto CRF based on resolution when quality='high'
if height >= 2160: auto_crf = '23'  # 4K - optimize size
elif height >= 1440: auto_crf = '20'  # 2K - high quality
else: auto_crf = '18'  # ≤1080p - max quality
```

**Hardware Encoder Selection:**
- QSV: Uses `-global_quality` (not `-crf`)
- NVENC: Uses `-cq` (not `-crf`)
- Software: Uses `-crf`

**Image Compression:**
- Pillow: `quality=95, optimize=True, subsampling=0`
- ImageMagick: `compression-level=9, compression-filter=5, sampling-factor=4:2:0`

## Developer Workflows

**Install globally:**
```bash
./media_converter.py --install  # Adds bash alias to ~/.bashrc
source ~/.bashrc
converter /path --resize 2k --delete-originals
```

**Testing hardware acceleration:**
```bash
ffmpeg -hide_banner -f lavfi -i nullsrc=s=256x256:d=1 -c:v h264_qsv -f null -
```

**Intel drivers for QSV:**
```bash
sudo apt install intel-media-va-driver-non-free i965-va-driver
```

**Command Examples**

**Standard usage (2K resize, auto-quality):**
```bash
converter /path/to/photos --resize 2k --remove-aae --delete-originals
```

**High-quality 4K preservation:**
```bash
converter /path/important --resize 4k --delete-originals
# Uses CRF 23 for 4K, maintains resolution
```

**Quality options:**
- `--video-quality high`: Auto CRF (18-23 based on resolution)
- `--video-quality medium`: CRF 23 for all
- `--resize 2k|1080p|4k|none`: Max height constraint, never upscales

## Key Conventions

1. **Never upscale videos**: Check `height > target_height` before applying scale filter
2. **Aspect ratio preservation**: Use `-2` for auto-calculated dimension: `scale=-2:1440`
3. **Even dimensions for codecs**: `scale=trunc(iw/2)*2:trunc(ih/2)*2`
4. **Confirmation pattern**: Requires uppercase 'YES' for destructive operations (now internationalized)
5. **File existence checks**: Skip conversion if output exists (no overwrite)

## Integration Points

**External dependencies:**
- FFmpeg: Video encoding/probing (required)
- ImageMagick: v6 (`convert`) or v7 (`magick`) auto-detected
- Pillow + pillow-heif: Optional, faster HEIC decoding

**Metadata preservation:**
Uses `touch -r original converted` to copy timestamps

## Common Issues

**HEVC playback issues:** Script forces H.264 (use_h264=True) for universal compatibility

**Size increase on 1080p:** Expected with CRF 18 when converting from HEVC. HEVC is ~50% more efficient than H.264.

**QSV not detected:** Check `/dev/dri/renderD128` exists, install intel-media-va-driver-non-free

## Internationalization

All user-facing messages, documentation, and code comments are now in English for global accessibility. Confirmation prompts for destructive actions now require 'YES' (uppercase) instead of 'SIM'.
