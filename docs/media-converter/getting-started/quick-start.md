# Quick Start

## Basic Usage

### Interactive Mode

```bash
converter
```

Follow the prompts to configure conversion settings.

### Convert a Directory

```bash
converter /path/to/photos
```

Uses defaults: JPEG 95% for images, H.264 for videos.

## Common Examples

### Image Conversion

```bash
# HEIC to JPEG 95% (default)
converter /path/photos --image-format JPEG

# Images only
converter /path/photos --only-images
```

### Video Conversion

```bash
# H.265 to H.264 (recommended)
converter /path/videos --video-codec h264

# High quality
converter /path/videos --video-quality high

# Resize 4K to 1080p
converter /path/4k-videos --resize 1080p
```

### Combined Operations

```bash
# Convert everything with optimal settings
converter /path/media --image-format JPEG --video-codec h264 --video-quality high

# Dry run first
converter /path/media --dry-run

# Delete originals after conversion
converter /path/media --delete-originals
```

## Default Behavior

| Setting | Default | Options |
|--------|---------|---------|
| Image format | JPEG 95% | JPEG, PNG |
| Video codec | H.264 | h264, h265, copy |
| Video quality | auto | auto, high, medium, lossless |
| Resize | none | 4k, 2k, 1080p, none |