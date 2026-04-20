# Image Conversion Guide

## Overview

The converter transforms HEIC/HEIF images to JPEG or PNG format, preserving EXIF metadata and orientation.

## Supported Formats

| Input | Output | Backend |
|-------|--------|---------|
| HEIC | JPEG 95% | Pillow (primary) |
| HEIC | PNG | Pillow (primary) |
| HEIF | JPEG 95% | Pillow (primary) |
| HEIF | PNG | Pillow (primary) |

If Pillow is unavailable, ImageMagick is used as fallback.

## Quality Settings

### JPEG (95%)

Best balance between quality and file size. Visually lossless for most use cases.

### PNG (Lossless)

True lossless compression. Larger file sizes but perfect quality.

## EXIF Handling

- **Orientation**: Automatically corrected using PIL.ImageOps.exif_transpose
- **Metadata**: GPS, camera info, date/time preserved in JPEG
- **Color Space**: Automatic RGB conversion for RGBA images

## Batch Processing

```bash
# Convert all images in directory
converter /path/photos

# Images only (skip videos)
converter /path/photos --only-images

# PNG output
converter /path/photos --image-format PNG
```