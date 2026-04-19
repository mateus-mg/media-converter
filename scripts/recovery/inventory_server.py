#!/usr/bin/env python3
"""
Server Video Inventory Scanner

Scans all video files in Ellen and Mateus directories and extracts
metadata (dimensions, rotation, codec, creation_time, etc.) for
the recovery pipeline.

Output: data/inventory_server.json
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Directories to scan
SCAN_DIRS = [
    Path('/media/mateus/Servidor/Ellen/'),
    Path('/media/mateus/Servidor/Mateus/'),
]

# Video extensions to look for
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.hevc'}

# Output path
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'inventory_server.json'


def determine_source(path: Path) -> str:
    """Determine if a video is from 'ellen' or 'mateus' based on its path.

    Checks for the specific Servidor subdirectories.
    Note: /media/mateus/ is the user home, so we must check
    for /Servidor/Ellen/ or /Servidor/Mateus/ patterns specifically.
    """
    path_str = str(path)
    if '/Servidor/Ellen/' in path_str:
        return 'ellen'
    if '/Servidor/Mateus/' in path_str:
        return 'mateus'
    return 'unknown'


def extract_video_metadata(path: Path) -> Optional[Dict[str, Any]]:
    """Extract video metadata using ffprobe.

    Returns a dict with: path, filename, source, creation_time, duration,
    width, height, rotation, codec, bitrate, size.
    Returns None if ffprobe fails.
    """
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        str(path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.warning(f"ffprobe failed for: {path.name}")
            return None
        info = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        logger.warning(f"ffprobe error for {path.name}: {e}")
        return None

    # Extract video stream info
    width = 0
    height = 0
    codec = None
    rotation = 0

    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'video':
            width = int(stream.get('width', 0))
            height = int(stream.get('height', 0))
            codec = stream.get('codec_name')

            # Extract rotation from side_data_list
            for side in stream.get('side_data_list', []):
                if 'rotation' in side:
                    rotation = int(float(side['rotation']))
                    break
            break

    # Extract format info
    fmt = info.get('format', {})
    duration = float(fmt.get('duration', 0))
    bitrate = int(fmt.get('bit_rate', 0))

    # Extract creation_time from format.tags, then streams.tags
    creation_time = None
    tags = fmt.get('tags', {})
    if tags and 'creation_time' in tags:
        creation_time = tags['creation_time']
    else:
        # Try streams
        for stream in info.get('streams', []):
            stream_tags = stream.get('tags', {})
            if 'creation_time' in stream_tags:
                creation_time = stream_tags['creation_time']
                break

    file_size = path.stat().st_size if path.exists() else 0

    return {
        'path': str(path),
        'filename': path.name,
        'source': determine_source(path),
        'creation_time': creation_time,
        'duration': duration,
        'width': width,
        'height': height,
        'rotation': rotation,
        'codec': codec,
        'bitrate': bitrate,
        'size': file_size,
    }


def find_video_files(scan_dirs: List[Path] = None) -> List[Path]:
    """Find all video files in the scan directories."""
    if scan_dirs is None:
        scan_dirs = SCAN_DIRS

    video_files = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            logger.warning(f"Directory not found: {scan_dir}")
            continue
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(scan_dir.rglob(f'*{ext}'))

    return sorted(set(video_files))


def build_inventory(
    scan_dirs: List[Path] = None,
    output_path: Path = None,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Scan all videos and build the inventory.

    Args:
        scan_dirs: Directories to scan (default: Ellen + Mateus)
        output_path: Where to save the JSON (default: data/inventory_server.json)
        show_progress: Show tqdm progress bar

    Returns:
        List of video metadata dicts
    """
    if scan_dirs is None:
        scan_dirs = SCAN_DIRS
    if output_path is None:
        output_path = OUTPUT_PATH

    video_files = find_video_files(scan_dirs)
    logger.info(f"Found {len(video_files)} video files to scan")

    inventory = []
    failed = 0

    iterator = video_files
    if show_progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(video_files, desc="Scanning videos", unit="file")
        except ImportError:
            logger.info("tqdm not available, proceeding without progress bar")

    for vf in iterator:
        metadata = extract_video_metadata(vf)
        if metadata is not None:
            inventory.append(metadata)
        else:
            failed += 1

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=1)

    logger.info(f"Inventory complete: {len(inventory)} videos scanned, {failed} failed")
    logger.info(f"Saved to: {output_path}")

    # Print summary by source
    sources = {}
    for item in inventory:
        src = item['source']
        sources[src] = sources.get(src, 0) + 1
    for src, count in sorted(sources.items()):
        logger.info(f"  {src}: {count} videos")

    return inventory


if __name__ == '__main__':
    build_inventory()
