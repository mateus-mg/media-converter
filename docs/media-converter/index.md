# Media Converter

Universal HEIC & HEVC Converter - converts HEIC/HEIF images to JPEG 95% (or PNG) and H.265/HEVC videos to H.264 (maximum compatibility). Compatible with files from iOS, GoPro, DJI, Samsung, Sony, and other devices.

## Features

- **Smart Image Conversion**: HEIC/HEIF → JPEG/PNG with EXIF preservation
- **Video Transcoding**: H.265/HEVC → H.264 with hardware acceleration
- **Hardware Acceleration**: NVIDIA NVENC, Intel QSV, or software encoding
- **Automatic Quality**: Adaptive CRF based on source bitrate
- **Safety First**: Dry-run mode, confirmation prompts, trash instead of delete

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Architecture](architecture/overview.md)
- [CLI Reference](reference/cli.md)
- [Troubleshooting](guides/troubleshooting.md)

## Supported Formats

| Input | Output | Notes |
|-------|--------|-------|
| HEIC/HEIF | JPEG 95% / PNG | Pillow with pillow-heif backend |
| H.265/HEVC MOV/MP4 | H.264 MP4 | Codec detected via ffprobe |
| Other codecs | Skip | No unnecessary re-encoding |

## Hardware Acceleration

| Encoder | Best For | Performance |
|---------|----------|-------------|
| NVIDIA NVENC | 8-bit video | 3-5x faster than CPU |
| Intel QSV | Integrated GPU | 2-5x faster than CPU |
| Software (libx264) | 10-bit / DOVI | Maximum compatibility |

## License

This tool combines FFmpeg, ImageMagick/Pillow, and Python standard libraries.