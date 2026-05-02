# Media Converter — Project Knowledge Base

**Generated:** 2026-05-02  
**Commit:** 185303e  
**Branch:** fix/docs-links-and-badges

## OVERVIEW

Python CLI tool that converts HEIC/HEIF images to JPEG/PNG and H.265/HEVC videos to H.264. Features hardware acceleration (NVIDIA NVENC, Intel QSV), HDR tone mapping, and batch processing.

## STRUCTURE

```
media-converter/
├── scripts/              # Core Python modules
│   ├── media_converter.py    # Main conversion logic (2572 lines)
│   ├── cli_manager.py        # Interactive Rich CLI
│   ├── config.py             # Singleton config manager
│   ├── conversion_db.py      # JSON tracking database
│   ├── log_config.py         # Centralized logging
│   └── recovery/             # Recovery/squashed-detection subpackage
├── tests/                # Pytest test suite
├── docs/                 # MkDocs documentation source
├── data/                 # Runtime data (conversion_db.json)
├── logs/                 # Runtime logs
└── site/                 # Built documentation
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Image conversion | `scripts/media_converter.py` | HEIC/HEIF → JPEG 95% or PNG |
| Video conversion | `scripts/media_converter.py` | H.265 → H.264 with hardware accel |
| Interactive menu | `scripts/cli_manager.py` | Rich-based CLI interface |
| Config management | `scripts/config.py` | .env → Config singleton |
| Conversion tracking | `scripts/conversion_db.py` | JSON deduplication DB |
| Hardware detection | `scripts/media_converter.py:77-163` | NVENC/QSV auto-detection |
| HDR handling | `scripts/media_converter.py:166-193` | bt2020 + tone mapping |
| Tests | `tests/test_*.py` | pytest with fixtures |

## CONVENTIONS

- **Type hints:** Used throughout (`def func(x: int) -> str`)
- **Dataclasses:** For structured data (`NvidiaGPU`, `HardwareInfo`)
- **Singleton pattern:** `Config` class with `_instance`
- **Import fallbacks:** Try relative → absolute → graceful degrade
- **Rich logging:** Structured output with symbols (✓, !, ✗)
- **Path objects:** `pathlib.Path` preferred over string paths
- **Preserve metadata:** EXIF for images, dates for videos

## ANTI-PATTERNS (THIS PROJECT)

- **No in-place conversion:** CRITICAL comment at line 1175 — ffmpeg doesn't allow it
- **10-bit source protection:** Forces software encoder (NVENC/QSV limitations)
- **No overwriting:** Skips existing converted files with `_converted` suffix
- **Safety block:** Non-HEVC videos rejected even if caller misses filter

## UNIQUE STYLES

- **Flexible imports:** All modules use try/except for relative vs direct execution
- **Hardware cascade:** NVENC → QSV → Software (tested, not just detected)
- **Auto CRF by bitrate:** <10Mbps→18, 10-25→20, 25-50→22, >50→23
- **CRITICAL markers:** Used for safety-critical code sections

## COMMANDS

```bash
# Run tests
pytest tests/ -v

# Run interactive mode
./media-converter

# Convert with options
./media-converter /path/to/media --image-format JPEG --video-codec h264

# Build docs
mkdocs build --strict
mkdocs serve

# Install dependencies
pip install -r requirements.txt
```

## NOTES

- **Entry point:** `media-converter` bash wrapper → `scripts/cli_manager.py`
- **CI:** GitHub Actions runs pytest on Ubuntu + ffmpeg/imagemagick
- **Docs:** MkDocs Material deployed to GitHub Pages
- **No mypy/ruff:** Type hints present but no enforcement in CI
- **Virtual env:** `venv/` auto-activated by bash wrapper
- **Large file:** `media_converter.py` is 2572 lines — contains conversion logic, hardware detection, and video processing
