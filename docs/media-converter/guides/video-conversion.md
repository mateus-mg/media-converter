# Video Conversion Guide

## Overview

Converts H.265/HEVC videos to H.264 for maximum compatibility. Only processes videos with HEVC codec detected via ffprobe.

## Supported Formats

| Input | Output | Notes |
|-------|--------|-------|
| MOV (HEVC) | MP4 (H.264) | Re-encoded |
| MP4 (HEVC) | MP4 (H.264) | Re-encoded |
| MOV (H.264) | Skip | Not needed |
| MP4 (other) | Skip | Not needed |

## Codec Options

### H.264 (Recommended)

Maximum compatibility across all devices and platforms.

### H.265 (HEVC)

Better compression, smaller files. Good for archiving but limited device support.

### Copy (Remux)

No re-encoding. Fastest option but doesn't change codec.

## Hardware Acceleration

| Source | NVIDIA | Intel QSV | Software |
|--------|--------|-----------|----------|
| 8-bit | NVENC | QSV | libx264 |
| 10-bit | Software | Software | libx264 |
| DOVI | NVENC | Software | libx264 |

### Encoder Selection

| Quality | CRF | Use Case |
|---------|-----|----------|
| auto | 18-24 | Adaptive based on source bitrate |
| high | 18 | Visually lossless, recommended |
| medium | 23 | Good quality, smaller files |
| lossless | 18 | H.264 with CRF 18 (very large) |

## Resolution Options

| Option | Output Resolution | Best For |
|--------|------------------|----------|
| 4k | Original (keep) | Archive quality |
| 2k | 2560×1440 | Balance quality/speed |
| 1080p | 1920×1080 | Faster processing, smaller files |
| none | Original | Keep original resolution |