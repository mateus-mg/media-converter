# Troubleshooting

## Common Issues

### "Missing dependencies" error

```bash
# Verify installations
ffmpeg -version
convert --version

# Install on Ubuntu/Debian
sudo apt install ffmpeg imagemagick
```

### Hardware acceleration not detected

```bash
# Check available encoders
ffmpeg -hide_banner -encoders | grep -E "(qsv|nvenc)"

# Intel QSV drivers (Ubuntu)
sudo apt install intel-media-va-driver-non-free i965-va-driver
```

### HEIC conversion fails with Pillow

```bash
pip install --upgrade pillow pillow-heif
# ImageMagick fallback is auto-detected
```

### Video file size increased

- **Expected**: HEVC → H.264 typically increases size by ~30-50%
- **HEVC is 50% more efficient than H.264**
- **Solution**: Use `--video-codec h265` to maintain HEVC encoding

## Performance Tips

### Faster 4K conversion

```bash
converter /path/4k --resize 2k --video-quality medium
```

### Maximum quality

```bash
converter /path/media --image-format PNG --video-quality high --resize 4k
```

## Debug Mode

Enable verbose logging:

```bash
LOG_LEVEL=DEBUG converter /path/to/media
tail -f logs/media_converter.log
```