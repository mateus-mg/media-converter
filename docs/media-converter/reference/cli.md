# CLI Reference

## Command Structure

```bash
converter [directory] [options]
media-converter [directory] [options]
python3 scripts/cli_manager.py [command] [args]
```

## Options

### Image Options

| Option | Default | Description |
|--------|---------|-------------|
| `--image-format FORMAT` | JPEG | Output format: JPEG or PNG |
| `--only-images` | false | Process only images |

### Video Options

| Option | Default | Description |
|--------|---------|-------------|
| `--video-codec CODEC` | h264 | Codec: h264, h265, copy |
| `--video-quality QUALITY` | auto | Quality: auto, high, medium, lossless |
| `--resize RESOLUTION` | none | Resize: 4k, 2k, 1080p, none |
| `--only-videos` | false | Process only videos |

### Processing Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run` | false | Simulate without processing |
| `--delete-originals` | false | Delete originals after conversion |
| `--remove-aae` | false | Remove Apple .AAE files |
| `--install` | false | Install 'converter' globally |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 130 | Interrupted (Ctrl+C) |