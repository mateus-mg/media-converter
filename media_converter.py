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
from datetime import datetime
import argparse
import logging


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')


def log_message(level: str, msg: str) -> None:
    """Unified logging and terminal output"""
    color_map = {
        'INFO': Color.BLUE,
        'WARN': Color.YELLOW,
        'ERROR': Color.RED,
        'SUCCESS': Color.GREEN
    }
    color = color_map.get(level.upper(), Color.NC)
    print(f"{color}[{level.upper()}]{Color.NC} {msg}")


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


def count_files(directory: Path, filters: Optional[List[str]] = None, only_images: bool = False, only_videos: bool = False, only_hevc_videos: bool = False) -> Dict[str, int]:
    """Count files by extension that will actually be converted (excludes already converted files)"""
    counts = {'heic': 0, 'heif': 0, 'hevc': 0,
              'aae': 0, 'jpg': 0, 'jpeg': 0, 'png': 0}

    # Count image files to convert
    if not only_videos:
        for ext in ['heic', 'heif']:
            if filters and ext not in filters:
                continue

            image_files = list(directory.rglob(
                f"*.{ext}")) + list(directory.rglob(f"*.{ext.upper()}"))
            for img_file in image_files:
                # Check if already converted (case-insensitive search)
                if find_converted_file(img_file, ['.jpg', '.png', '.jpeg']):
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
            if find_converted_file(vid_file, ['.mp4']):
                continue

            # IMPORTANT: Check codec - only count H.265/HEVC videos for conversion
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


def is_16_9_aspect(width: int, height: int) -> bool:
    """Check if video has 16:9 aspect ratio"""
    if height == 0:
        return False
    aspect_ratio = width / height
    # 16:9 = 1.777... (tolerance of 0.01)
    return abs(aspect_ratio - (16/9)) < 0.01


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
                aae_file.unlink()
                stats['deleted'] += 1
                log_message('SUCCESS', f"Deleted: {aae_file.name}")
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

            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Save with maximum quality
            if output_format.upper() == 'PNG':
                # PNG: maximum lossless compression (reduces size without quality loss)
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPEG: quality 95 (great quality/size balance)
                img.save(output_path, 'JPEG', quality=95,
                         subsampling=0, optimize=True)

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
            # JPEG quality 95 (great quality/size balance)
            cmd = [
                imagemagick_cmd, str(input_path),
                '-quality', '95',
                '-auto-orient',
                '-filter', 'Lanczos',
                '-sampling-factor', '4:2:0',
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
    if not success and not output_path.exists():
        success, output_path = convert_image_imagemagick(
            input_path, output_format)

    return success, output_path


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


def convert_video(input_path: Path, codec: str = 'h264', quality: str = 'high', resize: str = 'none') -> Tuple[bool, Path]:
    """
    Converts video with maximum quality preserved

    Codec options:
    - h264: Maximum compatibility (RECOMMENDED)
    - h265 (HEVC): Best compression, superior quality, smaller files
    - copy: Remux only (no re-encoding)

    Quality options:
    - lossless: Lossless (very large files)
    - high: CRF 18 (visually lossless)
    - medium: CRF 23 (good quality)
    """
    output_path = input_path.with_suffix('.mp4')

    if output_path.exists() and output_path != input_path:
        log_message('WARN', f"File already exists: {output_path.name}")
        return False, output_path

    log_message('INFO', f"Converting video: {input_path.name}")

    # Get video information
    video_info = get_video_info(input_path)

    # Detect resolution
    width = 0
    height = 0
    duration = 0
    if video_info and 'streams' in video_info:
        for stream in video_info['streams']:
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                break
        if 'format' in video_info:
            duration = float(video_info['format'].get('duration', 0))

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
    hw_accel = check_hardware_acceleration()

    # Determine optimal preset based on hardware, resolution, and content
    def get_optimal_preset(hw_type: str, resolution_height: int, is_16_9: bool, codec_name: str) -> str:
        """
        Determine optimal preset based on:
        - Hardware: QSV/NVENC use fixed presets
        - Resolution: Higher = faster preset (quality already controlled by CRF)
        - Aspect: 16:9 = faster (more optimized by encoders)
        - Codec: h265 benefits from slower presets
        """
        # Hardware-specific presets
        if hw_type == 'nvenc':
            return 'p4'  # NVENC preset (p1-p7, p4 is balanced)

        if hw_type == 'qsv':
            return 'medium'  # QSV preset

        # Software encoding (libx264/libx265)
        if codec_name == 'h265':
            # H.265 benefits from slower presets for better compression
            if resolution_height >= 2160:  # 4K
                return 'medium'  # Faster for 4K (too slow otherwise)
            elif resolution_height >= 1440:  # 2K
                return 'slow'
            else:  # 1080p or less
                return 'slower'
        else:
            # H.264 preset selection
            if resolution_height >= 2160:  # 4K
                return 'fast' if is_16_9 else 'medium'
            elif resolution_height >= 1440:  # 2K
                return 'medium' if is_16_9 else 'slow'
            else:  # 1080p or less
                return 'slow' if is_16_9 else 'slower'

    # Check aspect ratio
    is_16_9 = is_16_9_aspect(width, height)
    optimal_preset = get_optimal_preset(hw_accel, height, is_16_9, codec)

    # Adjust quality automatically based on resolution
    auto_crf = None
    if quality == 'high':
        if height >= 2160:  # 4K
            auto_crf = '23'
            log_message(
                'INFO', f"  Auto quality set: CRF 23 (4K - size optimized)")
        elif height >= 1440:  # 2K
            auto_crf = '20'
            log_message(
                'INFO', f"  Auto quality set: CRF 20 (2K - high quality)")
        else:  # 1080p or smaller
            auto_crf = '18'
            log_message(
                'INFO', f"  Auto quality set: CRF 18 (≤1080p - maximum quality)")
    else:
        auto_crf = '23'

    # Configure video codec with hardware acceleration if available
    if codec == 'h264':
        if hw_accel == 'qsv':
            log_message(
                'INFO', f"  Using Intel Quick Sync Video (hardware acceleration, preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'h264_qsv',
                '-global_quality', auto_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high'
            ]
        elif hw_accel == 'nvenc':
            log_message(
                'INFO', f"  Using NVIDIA NVENC (hardware acceleration, preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'h264_nvenc',
                '-cq', auto_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high'
            ]
        elif quality == 'lossless':
            log_message('INFO', f"  Using software encoder (preset: medium)")
            video_codec = ['-c:v', 'libx264', '-qp', '0', '-preset', 'medium']
        else:
            log_message(
                'INFO', f"  Using software encoder (preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'libx264',
                '-crf', auto_crf,
                '-preset', optimal_preset,
                '-profile:v', 'high',
                '-level', '4.1'
            ]
    elif codec == 'h265':
        if quality == 'lossless':
            log_message('INFO', f"  Using H.265 lossless (preset: slower)")
            video_codec = ['-c:v', 'libx265', '-x265-params',
                           'lossless=1', '-preset', 'slower']
        else:
            crf = '18' if quality == 'high' else '23'
            log_message(
                'INFO', f"  Using H.265 encoder (preset: {optimal_preset})")
            video_codec = [
                '-c:v', 'libx265',
                '-crf', crf,
                '-preset', optimal_preset,
                '-x265-params', 'log-level=error'
            ]
    else:
        video_codec = ['-c:v', 'copy']

    # Configure audio codec (AAC high quality)
    if quality == 'lossless':
        audio_codec = ['-c:a', 'flac']
    else:
        audio_codec = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000']

    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-progress', 'pipe:1',
        *video_codec,
        *scale_filter,
        *audio_codec,
        '-movflags', '+faststart',
        '-map_metadata', '0',
        '-pix_fmt', 'yuv420p',
        '-y',
        str(output_path)
    ]

    log_message(
        'INFO', f"  Codec: {codec.upper()} | CRF: {auto_crf if quality != 'lossless' else 'lossless'} | Preset: medium")
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
        log_message('ERROR', f"Error converting video: {input_path.name}")
        if result.stderr:
            log_message('ERROR', f"  {result.stderr[-200:]}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path


def process_directory(
    directory: Path,
    image_format: str = 'JPEG',
    video_codec: str = 'h264',
    video_quality: str = 'high',
    dry_run: bool = False,
    delete_originals: bool = False,
    resize: str = 'none',
    only_images: bool = False,
    only_videos: bool = False,
    only_hevc_videos: bool = False
) -> Tuple[Dict[str, int], List[Path], List[Path]]:
    """
    Process all files in the directory

    Returns:
        Tuple containing:
        - stats: Dictionary with conversion statistics
        - converted_originals: List of files that were just converted
        - already_converted_originals: List of files that were already converted
    """
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

    # Process images
    image_extensions = []
    if not only_videos:
        log_message('INFO', "\n=== PROCESSING IMAGES ===")
        image_extensions = ['*.heic', '*.HEIC', '*.heif', '*.HEIF']

    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.rglob(ext))

    for img_file in sorted(image_files):
        # Check if converted file already exists (case-insensitive search)
        converted_file = find_converted_file(
            img_file, ['.jpg', '.png', '.jpeg'])

        if converted_file:
            log_message(
                'INFO',
                f"Skipping {img_file.name}: already converted to {converted_file.name}"
            )
            already_converted_originals.append(img_file)
            stats['images_skipped'] += 1
            continue

        # Convert new files
        if dry_run:
            log_message('INFO', f"[DRY RUN] Would convert: {img_file.name}")
            stats['images_converted'] += 1
        else:
            success, output_path = convert_image(
                img_file, use_png=(image_format.upper() == 'PNG')
            )
            if success:
                stats['images_converted'] += 1
                converted_originals.append(img_file)
            else:
                stats['images_failed'] += 1

    # Process videos (if not only_images)
    if not only_images:
        log_message('INFO', "\n=== PROCESSING VIDEOS ===")
        video_extensions = ['*.mov', '*.MOV', '*.mp4', '*.MP4']
        video_files = []
        for ext in video_extensions:
            video_files.extend(directory.rglob(ext))

        for vid_file in sorted(video_files):
            # Skip already converted files
            if '_converted' in vid_file.stem:
                continue

            # Check if output already exists (case-insensitive search for .mp4)
            converted_video = find_converted_file(vid_file, ['.mp4'])

            if converted_video:
                log_message(
                    'INFO',
                    f"Skipping {vid_file.name}: already converted to {converted_video.name}"
                )
                already_converted_originals.append(vid_file)
                stats['videos_skipped'] += 1
                continue

            # PRIMARY CRITERION: Check codec - only process H.265/HEVC videos
            info = get_video_info(vid_file)
            codec_name = None
            if info and 'streams' in info:
                for stream in info['streams']:
                    if stream.get('codec_type') == 'video':
                        codec_name = stream.get('codec_name')
                        break

            # Skip if NOT H.265/HEVC (already H.264 or other codec)
            if codec_name != 'hevc':
                log_message(
                    'INFO',
                    f"Skipping {vid_file.name}: codec {codec_name or 'unknown'} (not HEVC/H.265, no conversion needed)"
                )
                stats['videos_skipped'] += 1
                continue

            if dry_run:
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
                else:
                    stats['videos_failed'] += 1

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
        '--only-hevc-videos',
        action='store_true',
        help='Process only videos encoded in H.265/HEVC (GoPro, smartphones, etc)'
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
        default='PNG',
        help='Output format for images (default: JPEG 95%%)'
    )
    parser.add_argument(
        '--video-codec',
        choices=['h265', 'h264', 'copy'],
        default='h265',
        help='Codec for videos (default: h264 for maximum compatibility)'
    )
    parser.add_argument(
        '--video-quality',
        choices=['lossless', 'high', 'medium'],
        default='high',
        help='Video quality (default: high)'
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
    parser.add_argument(
        '--only-images',
        action='store_true',
        help='Process only images (HEIC/HEIF)'
    )
    parser.add_argument(
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

    # CORREÇÃO: Garantir que o padrão seja JPEG, não PNG
    # Apesar do parser definir PNG como padrão, vamos forçar JPEG
    if args.image_format.upper() == 'PNG' and not any(['--image-format' in arg for arg in sys.argv]):
        args.image_format = 'JPEG'
        log_message('INFO', "Using JPEG as default image format (95% quality)")

    # CORREÇÃO: Garantir que h264 seja o padrão real
    if args.video_codec == 'h265' and not any(['--video-codec' in arg for arg in sys.argv]):
        args.video_codec = 'h264'
        log_message(
            'INFO', "Using H.264 as default video codec (maximum compatibility)")

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
    hw_accel = check_hardware_acceleration()
    if hw_accel == 'qsv':
        log_message(
            'SUCCESS', "✓ Hardware acceleration: Intel Quick Sync Video detected!")
        log_message('INFO', "  Video conversion will be 2-5x faster")
    elif hw_accel == 'nvenc':
        log_message(
            'SUCCESS', "✓ Hardware acceleration: NVIDIA NVENC detected!")
        log_message('INFO', "  Video conversion will be 3-5x faster")
    elif hw_accel == 'vaapi':
        log_message('SUCCESS', "✓ Hardware acceleration: VAAPI detected!")
        log_message('INFO', "  Video conversion will be 2-3x faster")
    else:
        log_message('WARN', "⚠ Hardware acceleration not detected")
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
    total_files = sum(file_counts.values())

    if total_files == 0:
        log_message('WARN', "No HEIC, HEIF or H.265/HEVC videos found.")
        return 0

    print(f"\n{Color.CYAN}=== SUPPORTED FILES FOUND ==={Color.NC}")
    filtered_total = 0
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
            filtered_total += count
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
        print(f"  • MODE: Only videos will be converted (MOV/MP4 → H.264)")
        print(f"  • HEIC/HEIF will be ignored")
    else:
        print(f"  • HEIC/HEIF → JPEG 95% (great quality/size balance)")
        print(f"  • MOV/MP4 → H.264 (maximum compatibility)")

    quality_desc = {
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
    stats, converted_files, already_converted_files = process_directory(
        start_dir,
        image_format=args.image_format,
        video_codec=args.video_codec,
        video_quality=args.video_quality,
        dry_run=args.dry_run,
        delete_originals=args.delete_originals,
        resize=args.resize,
        only_images=args.only_images,
        only_videos=args.only_videos,
        only_hevc_videos=args.only_hevc_videos
    )

    # Handle .AAE files
    aae_stats = None
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
    elif args.remove_aae:
        aae_stats = remove_aae_files(start_dir, dry_run=True)

    # Centralized deletion logic - FIXED
    if args.delete_originals and (converted_files or already_converted_files) and not args.dry_run:
        print(f"\n{Color.CYAN}=== ORIGINAL FILES TO DELETE ==={Color.NC}")

        if converted_files:
            print(
                f"  {Color.GREEN}Files converted in this run:{Color.NC} {len(converted_files)}")
        if already_converted_files:
            print(
                f"  {Color.YELLOW}Files already converted (originals still present):{Color.NC} {len(already_converted_files)}")

        # Show newly converted originals
        if converted_files:
            print(f"\n{Color.GREEN}Newly converted originals:{Color.NC}")
            for original_file in sorted(converted_files):
                print(f"  - {original_file.name}")

        # Show already converted originals
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

            # Delete newly converted files
            for original_file in sorted(converted_files):
                try:
                    if original_file.exists():
                        # Verify converted file exists
                        possible_conversions = [
                            original_file.with_suffix('.jpg'),
                            original_file.with_suffix('.png'),
                            original_file.with_suffix('.mp4')
                        ]

                        converted_exists = False
                        for conv_file in possible_conversions:
                            if conv_file.exists() and conv_file.stat().st_size > 0 and conv_file != original_file:
                                converted_exists = True
                                break

                        if converted_exists:
                            log_message(
                                'INFO', f"Deleting: {original_file.name}")
                            original_file.unlink()
                            deleted_count += 1
                            log_message(
                                'SUCCESS', f"Deleted: {original_file.name}")
                        else:
                            log_message(
                                'ERROR', f"Converted file not found or invalid")
                            log_message(
                                'WARN', f"Skipping deletion of: {original_file.name}")
                    else:
                        log_message(
                            'WARN', f"File not found: {original_file.name}")
                except Exception as e:
                    log_message(
                        'ERROR', f"Error deleting {original_file.name}: {e}")
                    failed_delete += 1

            # Delete already converted files
            for original_file in sorted(already_converted_files):
                try:
                    if original_file.exists():
                        # Verify converted file exists
                        possible_conversions = [
                            original_file.with_suffix('.jpg'),
                            original_file.with_suffix('.png'),
                            original_file.with_suffix('.jpeg'),
                            original_file.with_suffix('.mp4')
                        ]

                        converted_exists = False
                        for conv_file in possible_conversions:
                            if conv_file.exists() and conv_file.stat().st_size > 0 and conv_file != original_file:
                                converted_exists = True
                                break

                        if converted_exists:
                            log_message(
                                'INFO', f"Deleting: {original_file.name}")
                            original_file.unlink()
                            deleted_count += 1
                            log_message(
                                'SUCCESS', f"Deleted: {original_file.name}")
                        else:
                            log_message(
                                'ERROR', f"Converted file not found or invalid")
                            log_message(
                                'WARN', f"Skipping deletion of: {original_file.name}")
                    else:
                        log_message(
                            'WARN', f"File not found: {original_file.name}")
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
    elif args.delete_originals and not converted_files and not already_converted_files:
        log_message('INFO', "No original files to delete.")

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
