# Module Reference

## Core Modules

### media_converter.py

**Purpose:** Core conversion engine for images and videos.

**Key Functions:**

| Function | Description |
|----------|-------------|
| `detect_full_hardware()` | Detect CPU, NVIDIA GPU, Intel GPU, and FFmpeg encoders |
| `convert_image()` | Convert HEIC/HEIF to JPEG/PNG using Pillow or ImageMagick |
| `convert_video()` | Convert H.265/HEVC to H.264 using FFmpeg |
| `process_directory()` | Batch process all files in a directory |
| `get_video_info()` | Get video metadata via ffprobe |

**Key Classes:** `NvidiaGPU`, `IntelGPU`, `HardwareInfo`

### cli_manager.py

**Purpose:** Rich-based interactive CLI interface.

**Key Class:** `CLIManager`

### config.py

**Purpose:** Singleton configuration manager loading from .env file.

**Key Properties:** `image_format`, `video_codec`, `video_quality`, `resize`

### conversion_db.py

**Purpose:** JSON-backed database for conversion history.

**Key Methods:** `record_conversion()`, `find_output_path()`, `is_converted()`

### log_config.py

**Purpose:** Centralized logging with Rich console and rotating file handler.

**Key Functions:** `get_logger()`, `log_success()`, `log_error()`, `log_warning()`

### interactive_helpers.py

**Purpose:** Shared prompt helpers for interactive mode.

**Key Functions:** `prompt_choice()`, `prompt_yes_no()`, `build_conversion_config()`

## Recovery Subsystem

Located in `scripts/recovery/`:

| Module | Purpose |
|--------|---------|
| `run_pipeline.py` | Pipeline orchestrator |
| `inventory_server.py` | Build inventory of server files |
| `inventory_recovered.py` | Build inventory from PhotoRec files |
| `find_pairs.py` | Find matching pairs |
| `detect_squashed.py` | Detect aspect ratio issues |
| `match_originals.py` | Match recovered with originals |
| `organize.py` | Organize matched files |
| `report.py` | Generate reports |