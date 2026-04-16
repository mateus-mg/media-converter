#!/usr/bin/env python3
"""
Universal HEIC & HEVC Converter
Converts HEIC/HEIF images to JPEG 95% (or PNG) and H.265/HEVC videos to H.264 (maximum compatibility)
Compatible with files from smartphones, GoPro, and other devices.
"""

from typing import Optional
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import logging

_hw_accel_cached = None


def send_to_trash(file_path: Path) -> bool:
    """Send a file to the system trash bin instead of permanently deleting it.

    Tries in order:
    1. send2trash library (cross-platform)
    2. gio trash (Linux/GNOME)
    3. trash-cli (Linux, any DE)
    4. Falls back to permanent deletion with warning
    """
    # Try send2trash library first
    try:
        import send2trash
        send2trash.send2trash(str(file_path))
        return True
    except ImportError:
        pass
    except Exception:
        pass

    # Try gio trash (Linux/GNOME)
    try:
        result = subprocess.run(
            ['gio', 'trash', str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try trash-cli (Linux, any desktop environment)
    try:
        result = subprocess.run(
            ['trash-put', str(file_path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: permanent deletion with warning
    log_message('WARN', f"No trash utility found — permanently deleting: {file_path.name}")
    try:
        file_path.unlink()
        return True
    except Exception:
        return False


# Import shared modules
try:
    from .interactive_helpers import build_conversion_config
    from .conversion_db import ConversionDatabase
    from .config import config, get_config
    from .log_config import get_logger as _get_logger
except ImportError:
    # Fallback for direct execution
    try:
        from interactive_helpers import build_conversion_config
        from conversion_db import ConversionDatabase
        from config import config, get_config
        from log_config import get_logger as _get_logger
    except ImportError:
        build_conversion_config = None
        ConversionDatabase = None
        config = None
        get_config = None
        _get_logger = None


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


_LOGGER = _get_logger(
    'MediaConverter') if _get_logger else logging.getLogger('MediaConverter')


def setup_logging(level=logging.INFO):
    """Setup logging level using the centralized logger."""
    _LOGGER.setLevel(level)


def _get_conversion_db_path() -> Path:
    """Return the JSON conversion database path and ensure parent directory exists."""
    project_root = Path(__file__).resolve().parent.parent
    if config is not None:
        db_file = getattr(config, 'conversion_db_file',
                          'data/conversion_db.json')
    else:
        db_file = 'data/conversion_db.json'
    db_path = project_root / db_file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def _get_conversion_db() -> Optional['ConversionDatabase']:
    """Create the conversion database helper when available."""
    if ConversionDatabase is None:
        return None
    return ConversionDatabase(_get_conversion_db_path())


def log_message(level: str, msg: str) -> None:
    """Unified log helper backed by centralized log_config wrappers."""
    message_text = str(msg)
    lines = message_text.split('\n')
    level_key = str(level).upper()

    level_map = {
        'SUCCESS': logging.INFO,
        'INFO': logging.INFO,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
    }
    symbol_map = {
        'SUCCESS': '✓',
        'WARN': '!',
        'ERROR': '✗',
    }
    log_level = level_map.get(level_key, logging.INFO)
    symbol = symbol_map.get(level_key, '')

    for line in lines:
        if line == '':
            _LOGGER.info('', stacklevel=2)
            continue

        payload = f"{symbol} {line}" if symbol else line
        _LOGGER.log(log_level, payload, stacklevel=2)


def _log_stage(cycle_label: str, stage: str) -> None:
    """Log a stage block using the same style as media-organizer."""
    log_message('INFO', '')
    log_message('INFO', '=' * 88)
    log_message('INFO', f"{cycle_label} | {stage}")
    log_message('INFO', '=' * 88)


def _log_cycle_progress(
    cycle_label: str,
    current: int,
    total: int,
    converted: int,
    skipped: int,
    failed: int,
    current_type: str,
    current_name: str,
) -> None:
    """Log periodic progress counters in a compact, structured line."""
    if total <= 0:
        percentage = 0.0
    else:
        percentage = (current / total) * 100.0
    log_message(
        'INFO',
        (
            f"{cycle_label} progress: {current}/{total} ({percentage:.1f}%) | "
            f"converted={converted} skipped={skipped} failed={failed} | "
            f"current_type={current_type} | current={current_name}"
        )
    )


def check_python_packages() -> bool:
    """Check if optional Python packages are installed"""
    missing_packages = []

    try:
        from PIL import Image
    except ImportError:
        missing_packages.append("pillow")

    try:
        import pillow_heif
    except ImportError:
        missing_packages.append("pillow-heif")

    if missing_packages:
        log_message(
            'WARN', f"Optional Python packages missing: {', '.join(missing_packages)}")
        log_message('INFO', "Install with: pip install pillow pillow-heif")
        log_message(
            'INFO', "Will use ImageMagick fallback for HEIC conversion.")
        return False

    log_message(
        'SUCCESS', "Python packages (Pillow, pillow-heif) are installed.")
    return True


def check_dependencies() -> bool:
    """Check if required dependencies are installed (ffmpeg, ffprobe, ImageMagick)"""
    missing_dependencies = []

    if not shutil.which('ffmpeg'):
        missing_dependencies.append("ffmpeg")
    if not shutil.which('ffprobe'):
        missing_dependencies.append("ffprobe (part of ffmpeg)")
    if not shutil.which('magick') and not shutil.which('convert'):
        missing_dependencies.append("ImageMagick")

    if missing_dependencies:
        log_message(
            'ERROR', f"Missing dependencies: {', '.join(missing_dependencies)}")
        log_message(
            'INFO', "Install missing dependencies using your package manager.")
        return False

    log_message('SUCCESS', "All required dependencies are installed.")

    # Check optional Python packages
    check_python_packages()

    return True


def check_hardware_acceleration() -> str:
    """Detect hardware acceleration support"""
    log_message('INFO', "Checking for hardware acceleration support...")
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=5
        )
        encoders = result.stdout

        if 'h264_qsv' in encoders:
            log_message('SUCCESS', "Intel Quick Sync (QSV) detected.")
            return 'qsv'
        if 'h264_nvenc' in encoders:
            log_message('SUCCESS', "NVIDIA NVENC detected.")
            return 'nvenc'
        if 'h264_vaapi' in encoders:
            log_message(
                'SUCCESS', "VAAPI (generic hardware acceleration) detected.")
            return 'vaapi'
    except subprocess.TimeoutExpired:
        log_message('WARN', "Hardware acceleration check timed out.")
    except Exception as e:
        log_message('ERROR', f"Error checking hardware acceleration: {e}")

    log_message(
        'INFO', "No hardware acceleration detected. Falling back to software encoding.")
    return 'none'


def get_hardware_acceleration() -> str:
    """Returns hardware acceleration with caching (doesn't change during session)."""
    global _hw_accel_cached
    if _hw_accel_cached is None:
        _hw_accel_cached = check_hardware_acceleration()
    return _hw_accel_cached


def count_files(directory: Path, filters: Optional[List[str]] = None, only_images: bool = False, only_videos: bool = False) -> Dict[str, int]:
    """Count files by extension that will actually be converted (excludes already converted files)"""
    counts = {'heic': 0, 'heif': 0, 'hevc': 0,
              'aae': 0, 'jpg': 0, 'jpeg': 0, 'png': 0}
    conversion_db = _get_conversion_db()

    # Count image files to convert
    if not only_videos:
        for ext in ['heic', 'heif']:
            if filters and ext not in filters:
                continue

            image_files = list(directory.rglob(
                f"*.{ext}")) + list(directory.rglob(f"*.{ext.upper()}"))
            for img_file in image_files:
                # Check if already converted (case-insensitive search)
                if find_recorded_converted_file(conversion_db, img_file, ['.jpg', '.png', '.jpeg']) or find_converted_file(img_file, ['.jpg', '.png', '.jpeg']):
                    continue
                counts[ext] += 1

    # Count video files to convert (by codec, not extension)
    if not only_images:
        video_exts = ['mov', 'mp4']
        all_video_files = []
        for ext in video_exts:
            all_video_files.extend(list(directory.rglob(
                f"*.{ext}")) + list(directory.rglob(f"*.{ext.upper()}")))

        hevc_count = 0
        for vid_file in all_video_files:
            # Skip files with _converted in name
            if '_converted' in vid_file.stem:
                continue

            # Check if already converted (case-insensitive search)
            if find_recorded_converted_file(conversion_db, vid_file, ['.mp4']) or find_converted_file(vid_file, ['.mp4']):
                continue

            # Always check codec - only H.265/HEVC videos are eligible for conversion
            info = get_video_info(vid_file)
            codec_name = None
            if info and 'streams' in info:
                for stream in info['streams']:
                    if stream.get('codec_type') == 'video':
                        codec_name = stream.get('codec_name')
                        break

            # Only count H.265/HEVC videos (these need conversion to H.264)
            if codec_name == 'hevc':
                hevc_count += 1

        # Store HEVC count in a dedicated counter (not duplicating in mov/mp4)
        counts['hevc'] = hevc_count

    # Count other file types (AAE, JPG, PNG) - always count all
    for ext in ['aae', 'jpg', 'jpeg', 'png']:
        if filters and ext not in filters:
            continue
        counts[ext] = len(list(directory.rglob(
            f"*.{ext}"))) + len(list(directory.rglob(f"*.{ext.upper()}")))

    return counts


def find_converted_file(original_file: Path, target_extensions: List[str]) -> Optional[Path]:
    """
    Find a converted file with case-insensitive search.
    Handles both uppercase and lowercase extensions.
    Returns the Path if found, None otherwise.
    """
    for ext in target_extensions:
        # Try exact case
        candidate = original_file.with_suffix(ext)
        if candidate.exists() and candidate != original_file and candidate.stat().st_size > 0:
            return candidate

        # Try case variations (for case-sensitive filesystems like Linux)
        parent = original_file.parent
        stem = original_file.stem

        # Check both lower and upper case variations of extension
        for ext_case in [ext.lower(), ext.upper()]:
            candidate_name = f"{stem}{ext_case}"
            candidate_path = parent / candidate_name
            if candidate_path.exists() and candidate_path != original_file and candidate_path.stat().st_size > 0:
                return candidate_path

    return None


def find_recorded_converted_file(
    db: Optional['ConversionDatabase'],
    original_file: Path,
    target_extensions: List[str]
) -> Optional[Path]:
    """Find a converted file using the JSON database, if available."""
    if db is None:
        return None

    recorded_output = db.find_output_path(original_file)
    if recorded_output and recorded_output.suffix.lower() in [ext.lower() for ext in target_extensions]:
        return recorded_output
    return None


def find_original_converted_output(
    original_file: Path,
    target_extensions: List[str],
    db: Optional['ConversionDatabase'] = None,
) -> Optional[Path]:
    """Resolve the converted output for an original file."""
    recorded_output = find_recorded_converted_file(
        db, original_file, target_extensions)
    if recorded_output:
        return recorded_output

    converted_file = find_converted_file(original_file, target_extensions)
    if converted_file:
        return converted_file

    parent = original_file.parent
    stem = original_file.stem

    if any(ext.lower() == '.mp4' for ext in target_extensions):
        candidate = parent / f"{stem}_converted.mp4"
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate

    for ext in target_extensions:
        for variant in (ext.lower(), ext.upper()):
            candidate = parent / f"{stem}{variant}"
            if candidate.exists() and candidate != original_file and candidate.stat().st_size > 0:
                return candidate

    return None


def is_16_9_aspect(width: int, height: int) -> bool:
    """Check if video has 16:9 aspect ratio"""
    if height == 0:
        return False
    aspect_ratio = width / height
    # 16:9 = 1.777... (tolerance of 0.01)
    return abs(aspect_ratio - (16/9)) < 0.01


def get_effective_dimensions(width: int, height: int, rotation: float) -> Tuple[int, int]:
    """Retorna dimensões efetivas considerando rotação.

    Vídeos de celular filmados em retrato têm rotação=90° mas dimensões brutas em paisagem.
    Esta função corrige as dimensões para refletir a orientação real de exibição.
    """
    if abs(rotation) in (90, 270):
        return height, width
    return width, height


def preserve_metadata(source: Path, destination: Path) -> None:
    """Preserve modification date from the original file"""
    try:
        stat_info = source.stat()
        os.utime(destination, (stat_info.st_atime, stat_info.st_mtime))
    except Exception as e:
        log_message('WARN', f"Could not preserve metadata: {e}")


def remove_aae_files(directory: Path, dry_run: bool = False) -> Dict[str, int]:
    """Remove .AAE files (Apple editing metadata)"""
    stats = {'deleted': 0, 'failed': 0}

    log_message('INFO', "\n=== REMOVING .AAE FILES ===")

    aae_files = list(directory.rglob('*.aae')) + list(directory.rglob('*.AAE'))

    if not aae_files:
        log_message('INFO', "No .AAE files found.")
        return stats

    log_message('INFO', f"Found {len(aae_files)} .AAE file(s)")

    for aae_file in sorted(aae_files):
        if dry_run:
            log_message('INFO', f"[DRY RUN] Would delete: {aae_file.name}")
            stats['deleted'] += 1
        else:
            try:
                log_message('INFO', f"Deleting: {aae_file.name}")
                send_to_trash(aae_file)
                stats['deleted'] += 1
                log_message('SUCCESS', f"Deleted (trashed): {aae_file.name}")
            except Exception as e:
                log_message('ERROR', f"Error deleting {aae_file.name}: {e}")
                stats['failed'] += 1

    return stats


def convert_image_pillow(input_path: Path, output_format: str = 'JPEG') -> Tuple[bool, Path]:
    """
    Converts HEIC/HEIF image using Pillow
    JPEG 95% is default for best quality/size balance
    PNG is available for lossless conversion
    """
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener
        register_heif_opener()

        ext = '.jpg' if output_format.upper() == 'JPEG' else '.png'
        output_path = input_path.with_suffix(ext)

        if output_path.exists():
            log_message('WARN', f"File already exists: {output_path.name}")
            return False, output_path

        log_message(
            'INFO', f"Converting: {input_path.name} → {output_path.name}")

        with Image.open(input_path) as img:
            # Apply EXIF orientation automatically
            if hasattr(img, 'getexif') and img.getexif() is not None:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)

            # Extract full EXIF data to preserve in output (GPS, camera info, date, etc.)
            exif_data = None
            try:
                if hasattr(img, 'getexif') and img.getexif() is not None:
                    exif_data = img.getexif().tobytes()
                    if not exif_data:
                        exif_data = None
            except Exception:
                exif_data = None

            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Save with maximum quality, preserving EXIF metadata
            if output_format.upper() == 'PNG':
                # PNG: maximum lossless compression (reduces size without quality loss)
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPEG: quality 95 (great quality/size balance), preserve EXIF
                save_kwargs = {
                    'quality': 95,
                    'subsampling': 0,
                    'optimize': True,
                }
                if exif_data:
                    save_kwargs['exif'] = exif_data
                img.save(output_path, 'JPEG', **save_kwargs)

        preserve_metadata(input_path, output_path)
        log_message('SUCCESS', f"Converted: {output_path.name}")
        return True, output_path

    except ImportError:
        log_message(
            'WARN', "Pillow/pillow-heif not available, using ImageMagick")
        return False, input_path
    except Exception as e:
        log_message('ERROR', f"Error converting with Pillow: {e}")
        return False, input_path


def convert_image_imagemagick(input_path: Path, output_format: str = 'JPEG') -> Tuple[bool, Path]:
    """
    Converts image using ImageMagick (fallback)
    """
    ext = '.jpg' if output_format.upper() == 'JPEG' else '.png'
    output_path = input_path.with_suffix(ext)

    if output_path.exists():
        log_message('WARN', f"File already exists: {output_path.name}")
        return False, output_path

    log_message('INFO', f"Converting: {input_path.name} → {output_path.name}")

    try:
        # Detect which command to use (magick for v7+ or convert for v6)
        imagemagick_cmd = 'magick' if shutil.which('magick') else 'convert'

        if output_format.upper() == 'PNG':
            # PNG with maximum lossless compression
            cmd = [
                imagemagick_cmd, str(input_path),
                '-auto-orient',
                '-filter', 'Lanczos',
                '-define', 'png:compression-level=9',
                '-define', 'png:compression-filter=5',
                '-define', 'png:compression-strategy=1',
                '-quality', '95',
                str(output_path)
            ]
        else:
            # JPEG quality 95 (great quality/size balance), preserve EXIF metadata
            cmd = [
                imagemagick_cmd, str(input_path),
                '-quality', '95',
                '-auto-orient',
                '-filter', 'Lanczos',
                '-sampling-factor', '4:2:0',
                # Preserve EXIF metadata (GPS, camera info, date)
                '-define', 'jpeg:preserve-exif=true',
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            preserve_metadata(input_path, output_path)
            log_message('SUCCESS', f"Converted: {output_path.name}")
            return True, output_path
        else:
            log_message('ERROR', f"Conversion failed: {input_path.name}")
            if output_path.exists():
                output_path.unlink()
            return False, input_path

    except Exception as e:
        log_message('ERROR', f"Error converting: {e}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path


def convert_image(input_path: Path, use_png: bool = False) -> Tuple[bool, Path]:
    """
    Converts HEIC/HEIF image to JPEG 95% (default) or PNG (lossless)
    Tries Pillow first, then ImageMagick as fallback
    """
    output_format = 'PNG' if use_png else 'JPEG'

    # Try with Pillow first (better quality)
    success, output_path = convert_image_pillow(input_path, output_format)

    # If Pillow fails, fall back to ImageMagick
    if not success:
        success, output_path = convert_image_imagemagick(
            input_path, output_format)

    return success, output_path


def get_optimal_preset(hw_type: str, resolution_height: int, is_16_9: bool, codec_name: str) -> str:
    """
    Determine optimal preset based on:
    - Hardware: preset profile can be adapted to resolution/content
    - Resolution: Higher = faster preset (quality already controlled by CRF)
    - Aspect: 16:9 = faster (more optimized by encoders)
    - Codec: h265 benefits from slower presets
    """
    if hw_type == 'nvenc':
        if resolution_height >= 2160:
            return 'p3'
        elif resolution_height >= 1440:
            return 'p4'
        else:
            return 'p5' if is_16_9 else 'p6'

    if hw_type == 'qsv':
        if resolution_height >= 2160:
            return 'fast'
        elif resolution_height >= 1440:
            return 'medium'
        else:
            return 'slow' if is_16_9 else 'slower'

    if codec_name == 'h265':
        if resolution_height >= 2160:
            return 'medium'
        elif resolution_height >= 1440:
            return 'slow'
        else:
            return 'slower'
    else:
        if resolution_height >= 2160:
            return 'fast' if is_16_9 else 'medium'
        elif resolution_height >= 1440:
            return 'medium' if is_16_9 else 'slow'
        else:
            return 'slow' if is_16_9 else 'slower'


def get_video_info(input_path: Path) -> Dict:
    """Get detailed video information"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(input_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception as e:
        log_message('WARN', f"Error getting video info: {e}")

    return {}


def _parse_ffprobe_rate(rate_value: Optional[str]) -> float:
    """Parse ffprobe frame rate values like '30000/1001' or '30'."""
    if not rate_value:
        return 0.0
    try:
        if '/' in str(rate_value):
            num_str, den_str = str(rate_value).split('/', 1)
            num = float(num_str)
            den = float(den_str)
            if den == 0:
                return 0.0
            return num / den
        return float(rate_value)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def _parse_ffprobe_int(value: Optional[str]) -> int:
    """Parse optional ffprobe integer fields safely."""
    try:
        return int(value) if value is not None else 0
    except (TypeError, ValueError):
        return 0


def _estimate_output_height(source_height: int, resize: str) -> int:
    """Estimate output height used by encoder decision logic."""
    resize_mode = str(resize).lower()
    if resize_mode == '1080p':
        return min(source_height, 1080)
    if resize_mode in {'2k', '1440p'}:
        return min(source_height, 1440)
    return source_height


def _adjust_preset_step(hw_type: str, current_preset: str, step: int) -> str:
    """Move preset faster/slower by step while preserving encoder-compatible names."""
    if step == 0:
        return current_preset

    if hw_type == 'nvenc':
        order = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7']
    elif hw_type == 'qsv':
        order = ['veryfast', 'faster', 'fast',
                 'medium', 'slow', 'slower', 'veryslow']
    else:
        order = ['fast', 'medium', 'slow', 'slower']

    if current_preset not in order:
        return current_preset

    idx = order.index(current_preset)
    new_idx = max(0, min(len(order) - 1, idx + step))
    return order[new_idx]


def _determine_auto_crf_and_preset(
    hw_type: str,
    base_preset: str,
    output_height: int,
    fps: float,
    bitrate_mbps: float,
    is_16_9: bool,
    pixel_format: str,
) -> Tuple[str, str, List[str]]:
    """Return adaptive CRF and preset tuned for quality/time balance."""
    reasons: List[str] = []

    # Base CRF by output resolution (targeting visually lossless quality)
    if output_height >= 2160:
        crf = 22
        reasons.append('base_crf=22_for_4k')
    elif output_height >= 1440:
        crf = 20
        reasons.append('base_crf=20_for_2k')
    else:
        crf = 18
        reasons.append('base_crf=18_for_1080p_or_lower')

    # Content complexity adjustments
    if fps >= 50.0:
        crf -= 1
        reasons.append('high_fps_keep_detail')
    elif fps > 0 and fps <= 24.5 and bitrate_mbps <= 6.0:
        crf += 1
        reasons.append('low_motion_allow_small_crf_relax')

    if bitrate_mbps >= 28.0:
        crf -= 1
        reasons.append('high_bitrate_source_preserve_texture')
    elif bitrate_mbps > 0 and bitrate_mbps <= 5.0 and output_height <= 1080:
        crf += 1
        reasons.append('low_bitrate_source_avoid_overspending_bits')

    if '10' in pixel_format or 'p010' in pixel_format:
        crf -= 1
        reasons.append('10bit_source_protect_gradients')

    crf = max(17, min(23, crf))

    # Preset tuning: keep speed-first baseline and only move when needed
    preset_step = 0
    if fps >= 50.0 or bitrate_mbps >= 28.0:
        preset_step += 1
        reasons.append('complex_content_one_step_slower')
    elif fps > 0 and fps <= 24.5 and bitrate_mbps > 0 and bitrate_mbps <= 5.0:
        preset_step -= 1
        reasons.append('simple_content_one_step_faster')

    if not is_16_9 and output_height <= 1080:
        preset_step += 1
        reasons.append('non_16_9_small_frame_one_step_slower')

    # Keep upper bound for very large outputs to avoid large time penalties
    if output_height >= 2160 and preset_step > 0:
        preset_step = 0
        reasons.append('4k_time_guard_keep_base_preset')

    tuned_preset = _adjust_preset_step(hw_type, base_preset, preset_step)
    return str(crf), tuned_preset, reasons


def _summarize_auto_factors(reasons: List[str]) -> str:
    """Build a concise, human-readable ranking of auto-tuning factors."""
    scores = {
        'resolution': 0,
        'fps': 0,
        'bitrate': 0,
        'pixel_format': 0,
        'aspect_ratio': 0,
        'time_guard': 0,
    }

    for reason in reasons:
        if 'base_crf' in reason:
            scores['resolution'] += 2
        if 'fps' in reason or 'motion' in reason:
            scores['fps'] += 2
        if 'bitrate' in reason:
            scores['bitrate'] += 2
        if '10bit' in reason or 'p010' in reason:
            scores['pixel_format'] += 1
        if '16_9' in reason:
            scores['aspect_ratio'] += 1
        if 'time_guard' in reason:
            scores['time_guard'] += 1

    labels = {
        'resolution': 'resolution',
        'fps': 'fps',
        'bitrate': 'bitrate',
        'pixel_format': 'pixel_format',
        'aspect_ratio': 'aspect_ratio',
        'time_guard': 'time_guard',
    }

    ranked = [
        labels[key]
        for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if score > 0
    ]
    if not ranked:
        return 'resolution'
    return ', '.join(ranked[:3])


def convert_video(input_path: Path, codec: str = 'h264', quality: str = 'auto', resize: str = 'none') -> Tuple[bool, Path]:
    """
    Converts video with maximum quality preserved

    Codec options:
    - h264: Maximum compatibility (RECOMMENDED)
    - h265 (HEVC): Best compression, superior quality, smaller files
    - copy: Remux only (no re-encoding)

    Quality options:
    - auto: Adaptive CRF by resolution (recommended)
    - lossless: Lossless (very large files)
    - high: CRF 18 (visually lossless)
    - medium: CRF 23 (good quality)
    """
    output_path = input_path.with_suffix('.mp4')

    # CRITICAL: Prevent in-place conversion (ffmpeg doesn't allow it)
    # If input is already .mp4, we need a different output name
    if output_path == input_path:
        # Generate alternative name with _converted suffix
        output_path = input_path.with_stem(f"{input_path.stem}_converted")

    if output_path.exists():
        log_message('WARN', f"File already exists: {output_path.name}")
        return False, output_path

    log_message('INFO', f"Converting video: {input_path.name}")

    # Get video information
    video_info = get_video_info(input_path)

    # Detect resolution
    width = 0
    height = 0
    duration = 0
    has_video_stream = False
    source_codec_name = None
    source_fps = 0.0
    source_pixel_format = 'unknown'
    source_bitrate_mbps = 0.0
    if video_info and 'streams' in video_info:
        for stream in video_info['streams']:
            if stream.get('codec_type') == 'video':
                has_video_stream = True
                source_codec_name = stream.get('codec_name')
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                source_fps = _parse_ffprobe_rate(
                    stream.get('avg_frame_rate') or stream.get('r_frame_rate')
                )
                source_pixel_format = str(
                    stream.get('pix_fmt', 'unknown')).lower()

                stream_bitrate = _parse_ffprobe_int(stream.get('bit_rate'))
                if stream_bitrate > 0:
                    source_bitrate_mbps = stream_bitrate / 1_000_000.0
                break
        if 'format' in video_info:
            duration = float(video_info['format'].get('duration', 0))
            if source_bitrate_mbps <= 0:
                format_bitrate = _parse_ffprobe_int(
                    video_info['format'].get('bit_rate'))
                if format_bitrate > 0:
                    source_bitrate_mbps = format_bitrate / 1_000_000.0

    # Safety net: never convert non-HEVC videos, even if a caller misses the filter.
    if source_codec_name != 'hevc':
        log_message(
            'WARN',
            f"Safety block: skipping {input_path.name} (source codec: {source_codec_name or 'unknown'}, required: hevc)"
        )
        return False, input_path

    if not has_video_stream or width <= 0 or height <= 0:
        log_message(
            'WARN',
            f"Skipping invalid or unreadable video input: {input_path.name}"
        )
        return False, input_path

    log_message('INFO', f"  Source codec validated: {source_codec_name}")

    # Warn if 4K (will take a while)
    if height >= 2160:
        file_size = input_path.stat().st_size / (1024 * 1024)
        log_message(
            'WARN', f"  4K video detected ({width}x{height}) — size: {file_size:.1f} MB")
        log_message(
            'WARN', f"  Estimated time: {duration * 0.5:.0f}-{duration * 1:.0f} minutes")
        if resize == 'none':
            log_message(
                'INFO', f"  Tip: use --resize 2k to speed up conversion (approx 3-4x)")

    # Determine output resolution
    scale_filter = []
    if resize != 'none' and resize != '4k':
        # Check if video is 16:9
        is_16_9 = is_16_9_aspect(width, height)

        if resize in ['2k', '1440p']:
            target_width = 2560
            target_height = 1440
        else:  # 1080p
            target_width = 1920
            target_height = 1080

        # Only resize if the video is LARGER than the target
        if height > target_height:
            if is_16_9:
                # Force exact resolution for 16:9 videos
                scale_filter = [
                    '-vf', f'scale={target_width}:{target_height}:flags=lanczos']
                log_message(
                    'INFO', f"  Resizing: {width}x{height} → {target_width}x{target_height} (16:9)")
            else:
                # Keep aspect ratio for non-16:9 videos
                scale_filter = [
                    '-vf', f'scale=-2:{target_height}:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2']
                log_message(
                    'INFO', f"  Resizing: {width}x{height} → height {target_height}px (keeping aspect ratio)")
        else:
            log_message(
                'INFO', f"  Keeping original resolution: {width}x{height} (already ≤ {target_height}px)")

    # Detect hardware acceleration
    hw_accel = get_hardware_acceleration()

    # Determine optimal preset based on hardware, resolution, and content
    # (function moved to module scope for clarity and reusability)

    # Check aspect ratio
    is_16_9 = is_16_9_aspect(width, height)
    output_height = _estimate_output_height(height, resize)
    optimal_preset = get_optimal_preset(
        hw_accel, output_height, is_16_9, codec)

    # Resolve quality mode and CRF strategy
    quality_mode = str(quality).lower()
    if quality_mode not in {'auto', 'high', 'medium', 'lossless'}:
        quality_mode = 'auto'

    selected_crf = '23'
    auto_reasons: List[str] = []
    if quality_mode == 'auto':
        selected_crf, optimal_preset, auto_reasons = _determine_auto_crf_and_preset(
            hw_type=hw_accel,
            base_preset=optimal_preset,
            output_height=output_height,
            fps=source_fps,
            bitrate_mbps=source_bitrate_mbps,
            is_16_9=is_16_9,
            pixel_format=source_pixel_format,
        )
        auto_factor_summary = _summarize_auto_factors(auto_reasons)
        log_message(
            'INFO',
            (
                f"  Auto tuning: out_h={output_height} | src_fps={source_fps:.2f} "
                f"| src_bitrate={source_bitrate_mbps:.2f}Mbps | pix_fmt={source_pixel_format}"
            )
        )
        log_message('INFO', f"  Auto factors: {auto_factor_summary}")
    elif quality_mode == 'high':
        selected_crf = '18'
        log_message('INFO', "  Manual quality: HIGH (CRF 18)")
    elif quality_mode == 'medium':
        selected_crf = '23'
        log_message('INFO', "  Manual quality: MEDIUM (CRF 23)")
    else:
        log_message('INFO', "  Manual quality: LOSSLESS")

    # Configure video codec with hardware acceleration if available
    if codec == 'h264':
        if hw_accel == 'qsv':
            log_message(
                'INFO', f"  Using Intel Quick Sync Video (hardware acceleration, preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'h264_qsv',
                '-global_quality', selected_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high'
            ]
        elif hw_accel == 'nvenc':
            log_message(
                'INFO', f"  Using NVIDIA NVENC (hardware acceleration, preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'h264_nvenc',
                '-cq', selected_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high'
            ]
        elif quality_mode == 'lossless':
            log_message('INFO', f"  Using software encoder (preset: medium)")
            video_codec = ['-c:v', 'libx264', '-qp', '0', '-preset', 'medium']
        else:
            log_message(
                'INFO', f"  Using software encoder (preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'libx264',
                '-crf', selected_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high',
                '-level', '4.1'
            ]
    elif codec == 'h265':
        if quality_mode == 'lossless':
            log_message('INFO', f"  Using H.265 lossless (preset: slower)")
            video_codec = ['-c:v', 'libx265', '-x265-params',
                           'lossless=1', '-preset', 'slower']
        else:
            log_message(
                'INFO', f"  Using H.265 encoder (preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'libx265',
                '-crf', selected_crf,
                '-preset', optimal_preset,
                '-x265-params', 'log-level=error'
            ]
    else:
        video_codec = ['-c:v', 'copy']

    # Configure audio codec (AAC high quality)
    if quality_mode == 'lossless':
        audio_codec = ['-c:a', 'flac']
    else:
        audio_codec = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000']

    # Detect rotation from video side_data (important for phone videos)
    rotation = 0
    if video_info and 'streams' in video_info:
        for stream in video_info['streams']:
            if stream.get('codec_type') == 'video':
                side_data_list = stream.get('side_data_list', [])
                for side in side_data_list:
                    if 'rotation' in side:
                        rotation = float(side['rotation'])
                        break
                break

    # Build transpose filter based on rotation metadata
    transpose_filter_str = None
    if rotation != 0:
        # ffmpeg transpose filter values:
        # 0 = 90° counter-clockwise + vertical flip (default)
        # 1 = 90° clockwise
        # 2 = 90° counter-clockwise
        # 3 = 90° clockwise + vertical flip
        if abs(rotation - 90) < 0.1:
            transpose_filter_str = 'transpose=1'
            log_message('INFO', f"  Rotation detected: {rotation}° → applying transpose=1 (90° CW)")
        elif abs(rotation + 90) < 0.1:
            transpose_filter_str = 'transpose=2'
            log_message('INFO', f"  Rotation detected: {rotation}° → applying transpose=2 (90° CCW)")
        elif abs(rotation - 180) < 0.1 or abs(rotation + 180) < 0.1:
            transpose_filter_str = 'transpose=2,transpose=2'
            log_message('INFO', f"  Rotation detected: {rotation}° → applying 180° rotation")
        elif abs(rotation - 270) < 0.1 or abs(rotation + 90) < 0.1:
            transpose_filter_str = 'transpose=2'
            log_message('INFO', f"  Rotation detected: {rotation}° → applying transpose=2 (270° CW = 90° CCW)")
        elif abs(abs(rotation) - 360) < 0.1:
            log_message('INFO', f"  Rotation detected: {rotation}° → no correction needed")
        else:
            log_message('WARN', f"  Unusual rotation: {rotation}° → skipping correction")

    # Combine scale and transpose filters into a single -vf chain
    video_filters = []
    filter_parts = []

    if scale_filter:
        # scale_filter is ['-vf', 'scale=...'] — extract just the filter part
        filter_parts.append(scale_filter[1])

    if transpose_filter_str:
        filter_parts.append(transpose_filter_str)

    if filter_parts:
        video_filters = ['-vf', ','.join(filter_parts)]

    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-progress', 'pipe:1',
        # Map all streams: video, audio, subtitles, data tracks
        '-map', '0:v?',
        '-map', '0:a?',
        '-map', '0:s?',
        '-map', '0:d?',
        *video_codec,
        *video_filters,
        *audio_codec,
        '-movflags', '+faststart',
        # Copy all metadata: container + per-stream (creation_time, handler_name, location, GPS, etc.)
        '-map_metadata', '0',
        '-map_metadata:s:v', '0:s:v',
        '-map_metadata:s:a', '0:s:a',
        # Copy chapters if present
        '-map_chapters', '0',
        '-pix_fmt', 'yuv420p',
        '-y',
        str(output_path)
    ]

    # Clear rotation metadata after applying transpose filter to prevent double-rotation in players
    if transpose_filter_str:
        cmd.extend(['-metadata:s:v', 'rotation=0'])

    crf_info = 'lossless' if quality_mode == 'lossless' else selected_crf
    log_message(
        'INFO', f"  Codec: {codec.upper()} | Quality: {quality_mode.upper()} | CRF: {crf_info} | Preset: {optimal_preset}")
    if height >= 2160:
        log_message('INFO', "  Processing 4K video... this may take a while")
    else:
        log_message('INFO', "  Converting... (this can take a few minutes)")

    import time
    start_time = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True,
                                text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        log_message(
            'ERROR', f"Timeout converting video (60 min): {input_path.name}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path

    elapsed_time = time.time() - start_time

    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        preserve_metadata(input_path, output_path)

        # Show size comparison
        original_size = input_path.stat().st_size / (1024 * 1024)
        converted_size = output_path.stat().st_size / (1024 * 1024)
        ratio = (converted_size / original_size) * 100
        log_message('SUCCESS', f"Converted: {output_path.name}")
        log_message(
            'INFO', f"  Original: {original_size:.2f} MB | Converted: {converted_size:.2f} MB ({ratio:.1f}%)")
        return True, output_path
    else:
        stderr_text = (result.stderr or '').strip()
        if 'Invalid data found when processing input' in stderr_text or 'Error opening input file' in stderr_text:
            log_message(
                'WARN', f"Skipping invalid video file: {input_path.name}")
        else:
            log_message('ERROR', f"Error converting video: {input_path.name}")
        if result.stderr:
            if 'Invalid data found when processing input' in stderr_text or 'Error opening input file' in stderr_text:
                log_message('WARN', f"  {result.stderr[-200:]}")
            else:
                log_message('ERROR', f"  {result.stderr[-200:]}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path


def process_directory(
    directory: Path,
    image_format: str = 'JPEG',
    video_codec: str = 'h264',
    video_quality: str = 'auto',
    dry_run: bool = False,
    delete_originals: bool = False,
    resize: str = 'none',
    only_images: bool = False,
    only_videos: bool = False,
) -> Tuple[Dict[str, int], List[Path], List[Path]]:
    """
    Process all files in the directory

    Returns:
        Tuple containing:
        - stats: Dictionary with conversion statistics
        - converted_originals: List of files that were just converted
        - already_converted_originals: List of files that were already converted
    """
    import time

    cycle_label = f"CONVERSION CYCLE | {directory}"
    cycle_start = time.time()

    stats = {
        'images_converted': 0,
        'videos_converted': 0,
        'images_failed': 0,
        'videos_failed': 0,
        'images_skipped': 0,
        'videos_skipped': 0
    }

    # Separate lists for tracking
    converted_originals = []  # Files converted in THIS run
    already_converted_originals = []  # Files that were ALREADY converted
    conversion_db = _get_conversion_db()

    _log_stage(cycle_label, "DISCOVERY START")

    # Discover images
    image_extensions = []
    if not only_videos:
        image_extensions = ['*.heic', '*.HEIC', '*.heif', '*.HEIF']

    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.rglob(ext))

    # Discover videos
    video_files = []
    if not only_images:
        video_extensions = ['*.mov', '*.MOV', '*.mp4', '*.MP4']
        for ext in video_extensions:
            video_files.extend(directory.rglob(ext))

    image_files_sorted = sorted(image_files)
    video_files_sorted = sorted(video_files)

    total_candidates = len(image_files_sorted) + len(video_files_sorted)
    log_message(
        'INFO',
        (
            f"Discovery summary: images={len(image_files_sorted)} "
            f"videos={len(video_files_sorted)} total={total_candidates} "
            f"mode(images_only={only_images} videos_only={only_videos})"
        )
    )
    _log_stage(cycle_label, "DISCOVERY END")

    if total_candidates == 0:
        log_message(
            'INFO', "No eligible files found in the selected directory.")
        _log_stage(cycle_label, "PROCESSING END")
        return stats, converted_originals, already_converted_originals

    _log_stage(cycle_label, "PROCESSING START")
    progress_current = 0
    progress_step = 10 if total_candidates >= 10 else 1

    if not only_videos:
        log_message('INFO', "=== PROCESSING IMAGES ===")
        if not image_files_sorted:
            log_message(
                'INFO', "No HEIC/HEIF image files found for conversion.")

    for img_file in image_files_sorted:
        progress_current += 1
        # Check if converted file already exists (case-insensitive search)
        converted_file = find_recorded_converted_file(
            conversion_db, img_file, ['.jpg', '.png', '.jpeg']) or find_converted_file(
            img_file, ['.jpg', '.png', '.jpeg'])

        if converted_file:
            log_message(
                'INFO',
                f"Skipping {img_file.name}: already converted to {converted_file.name}"
            )
            already_converted_originals.append(img_file)
            stats['images_skipped'] += 1
        elif dry_run:
            log_message('INFO', f"[DRY RUN] Would convert: {img_file.name}")
            stats['images_converted'] += 1
        else:
            success, output_path = convert_image(
                img_file, use_png=(image_format.upper() == 'PNG')
            )
            if success:
                stats['images_converted'] += 1
                converted_originals.append(img_file)
                if conversion_db is not None:
                    conversion_db.record_conversion(
                        img_file,
                        output_path,
                        file_type='image',
                        image_format=image_format,
                    )
            else:
                stats['images_failed'] += 1

        if progress_current == 1 or progress_current % progress_step == 0 or progress_current == total_candidates:
            _log_cycle_progress(
                cycle_label,
                progress_current,
                total_candidates,
                stats['images_converted'] + stats['videos_converted'],
                stats['images_skipped'] + stats['videos_skipped'],
                stats['images_failed'] + stats['videos_failed'],
                'image',
                img_file.name,
            )

    # Process videos (if not only_images)
    if not only_images:
        log_message('INFO', "=== PROCESSING VIDEOS ===")

        if not video_files_sorted:
            log_message('INFO', "No video files found for conversion.")

        for vid_file in video_files_sorted:
            progress_current += 1
            # Skip already converted files
            if '_converted' in vid_file.stem:
                stats['videos_skipped'] += 1
                if progress_current == 1 or progress_current % progress_step == 0 or progress_current == total_candidates:
                    _log_cycle_progress(
                        cycle_label,
                        progress_current,
                        total_candidates,
                        stats['images_converted'] + stats['videos_converted'],
                        stats['images_skipped'] + stats['videos_skipped'],
                        stats['images_failed'] + stats['videos_failed'],
                        'video',
                        vid_file.name,
                    )
                continue

            # Check if output already exists (case-insensitive search for .mp4)
            converted_video = find_recorded_converted_file(
                conversion_db, vid_file, ['.mp4']) or find_converted_file(vid_file, ['.mp4'])

            if converted_video:
                log_message(
                    'INFO',
                    f"Skipping {vid_file.name}: already converted to {converted_video.name}"
                )
                already_converted_originals.append(vid_file)
                stats['videos_skipped'] += 1
            else:
                # PRIMARY CRITERION: Check codec - only process H.265/HEVC videos
                info = get_video_info(vid_file)
                codec_name = None
                if info and 'streams' in info:
                    for stream in info['streams']:
                        if stream.get('codec_type') == 'video':
                            codec_name = stream.get('codec_name')
                            break

                if codec_name != 'hevc':
                    log_message(
                        'INFO',
                        f"Skipping {vid_file.name}: codec {codec_name or 'unknown'} (H.264 and other codecs are not processed)"
                    )
                    stats['videos_skipped'] += 1
                elif dry_run:
                    log_message(
                        'INFO', f"[DRY RUN] Would convert: {vid_file.name}")
                    stats['videos_converted'] += 1
                else:
                    success, output_path = convert_video(
                        vid_file, codec=video_codec, quality=video_quality, resize=resize
                    )
                    if success:
                        stats['videos_converted'] += 1
                        converted_originals.append(vid_file)
                        if conversion_db is not None:
                            conversion_db.record_conversion(
                                vid_file,
                                output_path,
                                file_type='video',
                                codec=video_codec,
                                quality=video_quality,
                                resize=resize,
                            )
                    else:
                        stats['videos_failed'] += 1

            if progress_current == 1 or progress_current % progress_step == 0 or progress_current == total_candidates:
                _log_cycle_progress(
                    cycle_label,
                    progress_current,
                    total_candidates,
                    stats['images_converted'] + stats['videos_converted'],
                    stats['images_skipped'] + stats['videos_skipped'],
                    stats['images_failed'] + stats['videos_failed'],
                    'video',
                    vid_file.name,
                )

    elapsed = time.time() - cycle_start
    log_message(
        'INFO',
        (
            f"{cycle_label} completed: "
            f"converted={stats['images_converted'] + stats['videos_converted']} "
            f"skipped={stats['images_skipped'] + stats['videos_skipped']} "
            f"failed={stats['images_failed'] + stats['videos_failed']} "
            f"duration={elapsed:.2f}s"
        )
    )
    _log_stage(cycle_label, "PROCESSING END")

    return stats, converted_originals, already_converted_originals


def install_command() -> int:
    """Installs the 'converter' command globally on the system"""
    script_dir = Path(__file__).parent.absolute()
    wrapper_path = script_dir / 'converter'
    alias_line = f"alias converter='{wrapper_path}'"
    bashrc_path = Path.home() / '.bashrc'

    print("\n" + "=" * 60)
    print("  INSTALLING 'converter' COMMAND")
    print("=" * 60 + "\n")

    # Check if wrapper exists
    if not wrapper_path.exists():
        log_message('ERROR', f"Wrapper file not found: {wrapper_path}")
        log_message('INFO', "Run the script normally first to create it.")
        return 1

    # Check if already exists
    if bashrc_path.exists():
        with open(bashrc_path, 'r') as f:
            content = f.read()
            if 'alias converter=' in content:
                log_message(
                    'INFO', "Alias 'converter' already exists in ~/.bashrc")
                log_message('INFO', "Updating...")
                lines = content.split('\n')
                lines = [line for line in lines if 'alias converter=' not in line]
                content = '\n'.join(lines)
                with open(bashrc_path, 'w') as fw:
                    fw.write(content)

    # Add new alias
    with open(bashrc_path, 'a') as f:
        f.write(f"\n# Media Converter\n{alias_line}\n")

    log_message('SUCCESS', "Alias added to ~/.bashrc")
    print()
    print("=" * 60)
    print(f"{Color.GREEN}  INSTALLATION COMPLETE!{Color.NC}")
    print("=" * 60)
    print()
    print("To use now, run:")
    print(f"  {Color.CYAN}source ~/.bashrc{Color.NC}")
    print()
    print("Or close and reopen the terminal.")
    print()
    print("Then you can use it from anywhere:")
    print(f"  {Color.GREEN}converter /path/to/photos{Color.NC}")
    print(f"  {Color.GREEN}converter --help{Color.NC}")
    print()

    return 0


def is_hevc_video(input_path: Path) -> bool:
    """Check whether a video file is encoded with HEVC/H.265."""
    video_info = get_video_info(input_path)
    if video_info and 'streams' in video_info:
        for stream in video_info['streams']:
            if stream.get('codec_type') == 'video':
                return stream.get('codec_name') == 'hevc'
    return False


def run_interactive_conversion(preselected_mode: Optional[str] = None) -> int:
    """
    Run the interactive conversion flow using shared configuration prompts.

    Args:
        preselected_mode: "images", "videos", or None for all files

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if build_conversion_config is None:
        log_message('ERROR', "Interactive helpers not available")
        return 1

    print(f"\n{Color.CYAN}🎬 Media Converter System{Color.NC}")
    print(f"{Color.CYAN}Setup Wizard{Color.NC}")
    print(f"{Color.CYAN}{'=' * 36}{Color.NC}\n")
    print(f"{Color.GREEN}Welcome to the Media Converter!{Color.NC}")
    print("This tool converts:")
    print("  - HEIC/HEIF images to JPEG/PNG")
    print("  - HEVC/H.265 videos to H.264 (universal)\n")

    # Build configuration through interactive prompts
    config = build_conversion_config(preselected_mode=preselected_mode)

    # Get path from user
    print(f"\n{Color.CYAN}Input Source{Color.NC}")
    while True:
        path_input = input(
            "Enter a file or folder path (or press Enter to cancel): ").strip()
        if not path_input:
            log_message('INFO', "Conversion cancelled.")
            return 0
        start_path = Path(path_input)
        if start_path.exists():
            break
        log_message('ERROR', f"Path not found: {start_path}")

    # Show summary
    print(f"\n{Color.CYAN}Conversion Settings Summary{Color.NC}")
    print(f"{Color.CYAN}{'─' * 40}{Color.NC}")
    print(f"Target path:       {Color.GREEN}{start_path}{Color.NC}")
    print(
        f"Image format:      {Color.GREEN}{config['image_format']}{Color.NC}")
    print(
        f"Video codec:       {Color.GREEN}{str(config['video_codec']).upper()}{Color.NC}")
    print(
        f"Video quality:     {Color.GREEN}{str(config['video_quality']).upper()}{Color.NC}")

    resize_display = "Original (keep)" if config['resize'] == 'none' else str(
        config['resize']).upper()
    print(f"Video resolution:  {Color.GREEN}{resize_display}{Color.NC}")
    print(
        f"Dry run:           {Color.GREEN}{'Yes' if config['dry_run'] else 'No'}{Color.NC}")
    print(
        f"Delete originals:  {Color.GREEN}{'Yes' if config['delete_originals'] else 'No'}{Color.NC}")
    print(
        f"Remove .AAE:       {Color.GREEN}{'Yes' if config['remove_aae'] else 'No'}{Color.NC}")
    print(f"{Color.CYAN}{'─' * 40}{Color.NC}")

    # Confirm
    confirm = input(
        f"\n{Color.YELLOW}Proceed with these settings? Type {Color.GREEN}YES{Color.YELLOW} to continue: {Color.NC}").strip()
    if confirm != 'YES':
        log_message('INFO', "Operation cancelled by user.")
        return 0

    # Handle single file
    if start_path.is_file():
        return _convert_single_file(config, start_path)

    # Handle directory - delegate to process_directory
    return _run_directory_conversion(config, start_path)


def _convert_single_file(config: Dict, file_path: Path) -> int:
    """Convert a single file with the provided configuration."""
    conversion_db = _get_conversion_db()
    image_extensions = {'.heic', '.heif'}
    video_extensions = {'.mov', '.mp4'}
    suffix = file_path.suffix.lower()

    if suffix in image_extensions:
        if config['only_videos']:
            log_message(
                'ERROR', "Image file provided, but video-only mode is enabled.")
            return 1
        converted_file = find_recorded_converted_file(
            conversion_db, file_path, ['.jpg', '.png', '.jpeg']) or find_converted_file(file_path, ['.jpg', '.png', '.jpeg'])
        if converted_file:
            log_message(
                'INFO', f"Already converted: {file_path.name} -> {converted_file.name}")
            return 0
        if config['dry_run']:
            log_message(
                'INFO', f"[DRY RUN] Would convert image: {file_path.name}")
            return 0
        success, output_path = convert_image(
            file_path,
            use_png=str(config['image_format']).upper() == 'PNG'
        )
        if success and conversion_db is not None:
            conversion_db.record_conversion(
                file_path,
                output_path,
                file_type='image',
                image_format='PNG' if str(
                    config['image_format']).upper() == 'PNG' else 'JPEG',
            )
    elif suffix in video_extensions:
        if config['only_images']:
            log_message(
                'ERROR', "Video file provided, but image-only mode is enabled.")
            return 1
        if not is_hevc_video(file_path):
            log_message('WARN', f"Skipping non-HEVC video: {file_path.name}")
            return 0
        converted_file = find_recorded_converted_file(
            conversion_db, file_path, ['.mp4']) or find_converted_file(file_path, ['.mp4'])
        if converted_file:
            log_message(
                'INFO', f"Already converted: {file_path.name} -> {converted_file.name}")
            return 0
        if config['dry_run']:
            log_message(
                'INFO', f"[DRY RUN] Would convert video: {file_path.name}")
            return 0
        success, output_path = convert_video(
            file_path,
            codec=str(config['video_codec']),
            quality=str(config['video_quality']),
            resize=str(config['resize'])
        )
        if success and conversion_db is not None:
            conversion_db.record_conversion(
                file_path,
                output_path,
                file_type='video',
                codec=str(config['video_codec']),
                quality=str(config['video_quality']),
                resize=str(config['resize']),
            )
    else:
        log_message('ERROR', f"Unsupported file type: {file_path.name}")
        return 1

    if not success:
        return 1

    if config['delete_originals']:
        confirm_delete = input(
            "To confirm deletion, type 'DELETE 1 FILES' in uppercase: "
        ).strip()
        if confirm_delete == 'DELETE 1 FILES':
            if output_path.exists() and output_path.stat().st_size > 0:
                send_to_trash(file_path)
                log_message('SUCCESS', f"Moved to trash: {file_path.name}")
            else:
                log_message(
                    'ERROR', "Converted file not found or invalid. Skipping deletion.")
        else:
            log_message('INFO', "Deletion cancelled by user.")

    return 0


def _run_directory_conversion(config: Dict, start_dir: Path) -> int:
    """Run conversion on a directory using process_directory."""
    # Banner
    print("\n" + "=" * 60)
    print("  UNIVERSAL HEIC & HEVC CONVERTER - MAXIMUM COMPATIBILITY")
    print("=" * 60 + "\n")

    # Check dependencies
    log_message('INFO', "Checking dependencies...")
    if not check_dependencies():
        return 1

    # Check hardware acceleration
    hw_accel = get_hardware_acceleration()
    if hw_accel == 'qsv':
        log_message(
            'SUCCESS', "Hardware acceleration: Intel Quick Sync Video detected!")
        log_message('INFO', "  Video conversion will be 2-5x faster")
    elif hw_accel == 'nvenc':
        log_message(
            'SUCCESS', "Hardware acceleration: NVIDIA NVENC detected!")
        log_message('INFO', "  Video conversion will be 3-5x faster")
    elif hw_accel == 'vaapi':
        log_message('SUCCESS', "Hardware acceleration: VAAPI detected!")
        log_message('INFO', "  Video conversion will be 2-3x faster")
    else:
        log_message('WARN', "Hardware acceleration not detected")
        log_message('INFO', "  Conversion will use CPU (slower, but works)")

    print()
    log_message('SUCCESS', "All dependencies are installed!\n")

    # Validate directory
    if not start_dir.exists() or not start_dir.is_dir():
        log_message('ERROR', f"Directory not found: {start_dir}")
        return 1

    # Process files
    log_message('INFO', "Starting conversion...\n")

    stats, converted_files, already_converted_files = process_directory(
        start_dir,
        image_format=config['image_format'],
        video_codec=config['video_codec'],
        video_quality=config['video_quality'],
        dry_run=config['dry_run'],
        delete_originals=config['delete_originals'],
        resize=config['resize'],
        only_images=config['only_images'],
        only_videos=config['only_videos']
    )

    # Handle .AAE files
    aae_stats = None
    if config['remove_aae'] and not config['dry_run']:
        aae_files = list(start_dir.rglob('*.AAE')) + \
            list(start_dir.rglob('*.aae'))
        if aae_files:
            print(f"\n{Color.CYAN}=== .AAE FILES FOUND ==={Color.NC}")
            log_message(
                'INFO', f"Found {len(aae_files)} Apple .AAE metadata file(s)")
            confirm_aae = input(
                f"{Color.YELLOW}Delete .AAE files? (type 'YES' in uppercase): {Color.NC}").strip()
            if confirm_aae == 'YES':
                aae_stats = remove_aae_files(start_dir, dry_run=False)
            else:
                log_message('INFO', ".AAE files preserved.")

    _handle_delete_originals(
        delete_originals=config['delete_originals'],
        dry_run=config['dry_run'],
        converted_files=converted_files,
        already_converted_files=already_converted_files,
        conversion_db=_get_conversion_db(),
    )

    # Final report
    print(f"\n{Color.CYAN}{'=' * 60}{Color.NC}")
    log_message('SUCCESS', "CONVERSION COMPLETE!")
    print(f"{Color.CYAN}{'=' * 60}{Color.NC}\n")

    print(
        f"{Color.GREEN}Images converted:{Color.NC} {stats['images_converted']}")
    print(
        f"{Color.GREEN}Videos converted:{Color.NC} {stats['videos_converted']}")

    if aae_stats:
        print(
            f"{Color.GREEN}.AAE files deleted:{Color.NC} {aae_stats['deleted']}")

    if stats['images_skipped'] > 0:
        print(
            f"{Color.YELLOW}Images already exist (skipped):{Color.NC} {stats['images_skipped']}")
    if stats['videos_skipped'] > 0:
        print(
            f"{Color.YELLOW}Videos already exist (skipped):{Color.NC} {stats['videos_skipped']}")

    if stats['images_failed'] > 0:
        print(
            f"{Color.RED}Images with error:{Color.NC} {stats['images_failed']}")
    if stats['videos_failed'] > 0:
        print(
            f"{Color.RED}Videos with error:{Color.NC} {stats['videos_failed']}")

    print()
    return 0


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description='Media Converter for Universal Formats with Maximum Quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
    %(prog)s /path/to/photos
    %(prog)s /path/to/photos --image-format jpeg --video-codec h264
    %(prog)s /path/to/photos --video-quality lossless
    %(prog)s /path/to/photos --resize 2k --video-quality medium
    %(prog)s /path/to/photos --dry-run

Image formats:
    JPEG - High quality 95%% compression (recommended, smaller files)
    PNG  - Lossless (larger files)

Video codecs:
    h264 - H.264, maximum compatibility (recommended)
    h265 - HEVC, best compression and quality
    copy - Remux only, no re-encoding

Video quality:
    auto     - Adaptive by resolution (recommended)
    lossless - Lossless (very large files)
    high     - CRF 18, visually lossless (recommended)
    medium   - CRF 23, good quality, smaller files

Video resizing:
    4k       - Keep original resolution (default)
    2k/1440p - 2560x1440 (best quality/speed balance)
    1080p    - 1920x1080 (faster, smaller size)
            """
    )
    parser.add_argument(
        'directory',
        nargs='?',
        type=Path,
        help='Directory containing files to convert'
    )
    parser.add_argument(
        '--image-format',
        choices=['PNG', 'JPEG', 'png', 'jpeg'],
        default='JPEG',
        help='Output format for images (default: JPEG 95%%)'
    )
    parser.add_argument(
        '--video-codec',
        choices=['h265', 'h264', 'copy'],
        default='h264',
        help='Codec for videos (default: h264 for maximum compatibility)'
    )
    parser.add_argument(
        '--video-quality',
        choices=['auto', 'lossless', 'high', 'medium'],
        default='auto',
        help='Video quality (default: auto)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate conversion without processing files'
    )
    parser.add_argument(
        '--delete-originals',
        action='store_true',
        help='CAUTION: Delete original files after successful conversion'
    )
    parser.add_argument(
        '--remove-aae',
        action='store_true',
        help='Remove .AAE files (Apple editing metadata)'
    )
    parser.add_argument(
        '--resize',
        choices=['4k', '2k', '1440p', '1080p', 'none'],
        default='none',
        help='Resize videos: 4k (keep), 2k/1440p (2560x1440), 1080p (1920x1080)'
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--only-images',
        action='store_true',
        help='Process only images (HEIC/HEIF)'
    )
    mode_group.add_argument(
        '--only-videos',
        action='store_true',
        help='Process only videos (MOV/MP4)'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install \'converter\' command globally on the system'
    )

    args = parser.parse_args()

    # Note: argparse defaults (JPEG for images, h264 for video) are applied automatically.
    # No manual override needed - if user passes --image-format or --video-codec,
    # argparse uses those values; otherwise, defaults are used.

    # If install, run and exit
    if args.install:
        return install_command()

    # Banner
    print("\n" + "=" * 60)
    print("  UNIVERSAL HEIC & HEVC CONVERTER - MAXIMUM COMPATIBILITY")
    print("=" * 60 + "\n")

    # Check dependencies
    log_message('INFO', "Checking dependencies...")
    if not check_dependencies():
        return 1

    # Check hardware acceleration
    hw_accel = get_hardware_acceleration()
    if hw_accel == 'qsv':
        log_message(
            'SUCCESS', "Hardware acceleration: Intel Quick Sync Video detected!")
        log_message('INFO', "  Video conversion will be 2-5x faster")
    elif hw_accel == 'nvenc':
        log_message(
            'SUCCESS', "Hardware acceleration: NVIDIA NVENC detected!")
        log_message('INFO', "  Video conversion will be 3-5x faster")
    elif hw_accel == 'vaapi':
        log_message('SUCCESS', "Hardware acceleration: VAAPI detected!")
        log_message('INFO', "  Video conversion will be 2-3x faster")
    else:
        log_message('WARN', "Hardware acceleration not detected")
        log_message('INFO', "  Conversion will use CPU (slower, but works)")

    print()

    log_message('SUCCESS', "All dependencies are installed!\n")

    # Get directory
    if args.directory:
        start_dir = args.directory
    else:
        dir_input = input(
            "Enter the folder path to search for files: ").strip()
        start_dir = Path(dir_input)

    # Validate directory
    if not start_dir.exists() or not start_dir.is_dir():
        log_message('ERROR', f"Directory not found: {start_dir}")
        return 1

    # Show all file extensions found
    print(f"\n{Color.CYAN}=== ALL FILE TYPES FOUND ==={Color.NC}")
    from collections import Counter
    all_files = list(start_dir.rglob("*"))
    ext_counter = Counter(f.suffix.lower()
                          for f in all_files if f.is_file() and f.suffix)
    if ext_counter:
        for ext, count in sorted(ext_counter.items(), key=lambda x: (-x[1], x[0])):
            print(
                f"  {ext[1:].upper() if ext.startswith('.') else ext.upper()}: {count} file(s)")
        print(
            f"  {Color.MAGENTA}TOTAL: {sum(ext_counter.values())} file(s){Color.NC}\n")
    else:
        log_message('WARN', "No files found in the directory.")
        return 0

    # Show filtered summary
    shown_types = []
    if args.only_images:
        shown_types = ['heic', 'heif']
    elif args.only_videos:
        shown_types = ['hevc']
    else:
        shown_types = ['heic', 'heif', 'hevc']

    log_message(
        'INFO', f"Searching for HEIC/HEIF files and H.265/HEVC videos in: {start_dir}")
    file_counts = count_files(start_dir, shown_types)
    filtered_total = sum(file_counts.get(ext, 0) for ext in shown_types)

    if filtered_total == 0:
        log_message('WARN', "No HEIC, HEIF or H.265/HEVC videos found.")
        return 0

    print(f"\n{Color.CYAN}=== SUPPORTED FILES FOUND ==={Color.NC}")
    for ext in shown_types:
        count = file_counts.get(ext, 0)
        if count > 0:
            if ext == 'hevc':
                display_name = 'H.265/HEVC videos'
            elif ext in ['heic', 'heif']:
                display_name = f'{ext.upper()} images'
            else:
                display_name = ext.upper()
            print(f"  {display_name}: {count} file(s)")
    print(f"  {Color.MAGENTA}TOTAL: {filtered_total} file(s) to convert{Color.NC}\n")

    # Show settings
    print(f"{Color.CYAN}=== SETTINGS ==={Color.NC}")
    print(f"  Image format: {args.image_format.upper()}")
    print(f"  Video codec: {args.video_codec.upper()}")
    print(f"  Video quality: {args.video_quality.upper()}")
    if args.resize != 'none':
        print(f"  Resize videos: {args.resize.upper()}")
    else:
        print("  Resize videos: None (keep original resolution)")
    if args.dry_run:
        print(
            f"  {Color.YELLOW}DRY RUN MODE (simulation only, no files will be processed){Color.NC}")
    print(f"  Process only images: {'Yes' if args.only_images else 'No'}")
    print(f"  Process only videos: {'Yes' if args.only_videos else 'No'}")
    print("  Video source filter: HEVC/H.265 only (H.264 is always skipped)")
    print(
        f"  Delete originals after conversion: {'Yes' if args.delete_originals else 'No'}")
    print(f"  Remove .AAE files: {'Yes' if args.remove_aae else 'No'}")
    print()

    # Show actions
    print(f"{Color.CYAN}=== ACTIONS TO BE PERFORMED ==={Color.NC}")
    if args.only_images:
        print(f"  • MODE: Only images will be converted (HEIC/HEIF → JPEG 95%)")
        print(f"  • MOV/MP4 will be ignored")
    elif args.only_videos:
        print(f"  • MODE: Only HEVC/H.265 videos will be converted (MOV/MP4 → H.264)")
        print(f"  • H.264 videos will be ignored")
    else:
        print(f"  • HEIC/HEIF → JPEG 95% (great quality/size balance)")
        print(
            f"  • MOV/MP4 → H.264 (H.264 videos are skipped; only HEVC/H.265 is processed)")

    quality_desc = {
        'auto': 'adaptive by resolution (recommended)',
        'lossless': 'truly lossless (very large files)',
        'high': 'CRF 18 - visually lossless (recommended)',
        'medium': 'CRF 23 - good quality, smaller size'
    }
    print(f"  • Quality: {quality_desc[args.video_quality]}")
    if args.resize != 'none':
        resize_desc = {
            '4k': 'keep 4K',
            '2k': 'max 1440p (2K)',
            '1440p': 'max 1440p (2K)',
            '1080p': 'max 1080p (Full HD)'
        }
        print(
            f"  • Resizing: {resize_desc.get(args.resize, args.resize)}")
    print(f"  • Automatic EXIF orientation correction")
    print(f"  • Metadata and original date preservation")
    print()

    # Confirm
    if not args.dry_run:
        confirm = input(
            "Proceed with conversion? Type YES to continue: ").strip()
        if confirm != 'YES':
            log_message('INFO', "Conversion cancelled by user.")
            return 0
        print()

    # Process files
    log_message('INFO', "Starting conversion...\n")
    conversion_db = _get_conversion_db()
    stats, converted_files, already_converted_files = process_directory(
        start_dir,
        image_format=args.image_format,
        video_codec=args.video_codec,
        video_quality=args.video_quality,
        dry_run=args.dry_run,
        delete_originals=args.delete_originals,
        resize=args.resize,
        only_images=args.only_images,
        only_videos=args.only_videos
    )

    # Handle .AAE files
    aae_stats = None
    if args.remove_aae and not args.only_videos:
        if not args.dry_run:
            aae_files = list(start_dir.rglob('*.AAE')) + \
                list(start_dir.rglob('*.aae'))

            if aae_files:
                print(f"\n{Color.CYAN}=== .AAE FILES FOUND ==={Color.NC}")
                log_message(
                    'INFO', f"Found {len(aae_files)} Apple .AAE metadata file(s)")
                log_message(
                    'INFO', "These files contain edits made in the Photos app")

                confirm_aae = input(
                    f"{Color.YELLOW}Delete .AAE files? (type 'YES' in uppercase): {Color.NC}"
                ).strip()

                if confirm_aae == 'YES':
                    aae_stats = remove_aae_files(start_dir, dry_run=False)
                else:
                    log_message('INFO', ".AAE files preserved.")
        else:
            aae_stats = remove_aae_files(start_dir, dry_run=True)
    elif args.remove_aae and args.only_videos:
        log_message(
            'INFO', "AAE removal skipped: videos-only mode does not process image metadata."
        )

    _handle_delete_originals(
        delete_originals=args.delete_originals,
        dry_run=args.dry_run,
        converted_files=converted_files,
        already_converted_files=already_converted_files,
        conversion_db=conversion_db,
    )

    # Final report
    print(f"\n{Color.CYAN}{'=' * 60}{Color.NC}")
    log_message('SUCCESS', "CONVERSION COMPLETE!")
    print(f"{Color.CYAN}{'=' * 60}{Color.NC}\n")

    print(
        f"{Color.GREEN}Images converted:{Color.NC} {stats['images_converted']}")
    print(
        f"{Color.GREEN}Videos converted:{Color.NC} {stats['videos_converted']}")

    if aae_stats:
        print(
            f"{Color.GREEN}.AAE files deleted:{Color.NC} {aae_stats['deleted']}")

    if stats['images_skipped'] > 0:
        print(
            f"{Color.YELLOW}Images already exist (skipped):{Color.NC} {stats['images_skipped']}")
    if stats['videos_skipped'] > 0:
        print(
            f"{Color.YELLOW}Videos already exist (skipped):{Color.NC} {stats['videos_skipped']}")

    if stats['images_failed'] > 0:
        print(
            f"{Color.RED}Images with error:{Color.NC} {stats['images_failed']}")
    if stats['videos_failed'] > 0:
        print(
            f"{Color.RED}Videos with error:{Color.NC} {stats['videos_failed']}")
    if aae_stats and aae_stats['failed'] > 0:
        print(
            f"{Color.RED}.AAE files with error:{Color.NC} {aae_stats['failed']}")

    print()
    return 0


def _handle_delete_originals(
    delete_originals: bool,
    dry_run: bool,
    converted_files: List[Path],
    already_converted_files: List[Path],
    conversion_db: Optional['ConversionDatabase'] = None,
) -> None:
    """Prompt and delete original files after a directory conversion cycle."""
    if delete_originals and (converted_files or already_converted_files) and not dry_run:
        print(f"\n{Color.CYAN}=== ORIGINAL FILES TO DELETE ==={Color.NC}")

        if converted_files:
            print(
                f"  {Color.GREEN}Files converted in this run:{Color.NC} {len(converted_files)}")
        if already_converted_files:
            print(
                f"  {Color.YELLOW}Files already converted (originals still present):{Color.NC} {len(already_converted_files)}")

        if converted_files:
            print(f"\n{Color.GREEN}Newly converted originals:{Color.NC}")
            for original_file in sorted(converted_files):
                print(f"  - {original_file.name}")

        if already_converted_files:
            print(
                f"\n{Color.YELLOW}Already converted originals (can also be deleted):{Color.NC}")
            for original_file in sorted(already_converted_files):
                print(f"  - {original_file.name}")

        print()
        total_to_delete = len(converted_files) + len(already_converted_files)
        confirm_delete = input(
            f"{Color.RED}Delete {total_to_delete} original file(s)? "
            f"Type 'YES' to confirm: {Color.NC}"
        ).strip()

        if confirm_delete == 'YES':
            deleted_count = 0
            failed_delete = 0

            for original_file in sorted(converted_files):
                try:
                    if not original_file.exists():
                        log_message(
                            'WARN', f"File not found: {original_file.name}")
                        continue

                    converted_output = find_original_converted_output(
                        original_file,
                        ['.jpg', '.png', '.jpeg', '.mp4'],
                        db=conversion_db,
                    )

                    if converted_output:
                        log_message('INFO', f"Deleting: {original_file.name}")
                        send_to_trash(original_file)
                        deleted_count += 1
                        log_message(
                            'SUCCESS', f"Moved to trash: {original_file.name}")
                    else:
                        log_message(
                            'WARN', f"Converted file not found for deletion: {original_file.name}")
                except Exception as e:
                    log_message(
                        'ERROR', f"Error deleting {original_file.name}: {e}")
                    failed_delete += 1

            for original_file in sorted(already_converted_files):
                try:
                    if not original_file.exists():
                        log_message(
                            'WARN', f"File not found: {original_file.name}")
                        continue

                    converted_output = find_original_converted_output(
                        original_file,
                        ['.jpg', '.png', '.jpeg', '.mp4'],
                        db=conversion_db,
                    )

                    if converted_output:
                        log_message('INFO', f"Deleting: {original_file.name}")
                        send_to_trash(original_file)
                        deleted_count += 1
                        log_message(
                            'SUCCESS', f"Moved to trash: {original_file.name}")
                    else:
                        log_message(
                            'WARN', f"Converted file not found for deletion: {original_file.name}")
                except Exception as e:
                    log_message(
                        'ERROR', f"Error deleting {original_file.name}: {e}")
                    failed_delete += 1

            print(
                f"\n{Color.GREEN}Files successfully deleted:{Color.NC} {deleted_count}")
            if failed_delete > 0:
                print(f"{Color.RED}Failed to delete:{Color.NC} {failed_delete}")
        else:
            log_message('INFO', "Deletion cancelled by user.")
    elif delete_originals and not converted_files and not already_converted_files:
        log_message('INFO', "No original files to delete.")


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log_message('WARN', "\n\nConversion interrupted by user.")
        sys.exit(130)
    except Exception as e:
        log_message('ERROR', f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
