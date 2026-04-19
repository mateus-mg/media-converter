#!/usr/bin/env python3
"""
Recovered Video Inventory Scanner

Scans all video files recovered by PhotoRec in /home/mateus/recup_dir.*/
and extracts metadata for the recovery pipeline.

Output: data/inventory_recovered.json
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# PhotoRec recovery directories
RECOVERY_BASE = Path('/home/mateus')
RECOVERY_PATTERN = 'recup_dir.*'

# Output path
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'inventory_recovered.json'


def extract_video_metadata(path: Path) -> Optional[Dict[str, Any]]:
    """Extract video metadata using ffprobe.

    Returns None if ffprobe fails or file has no valid video stream.
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
            return None
        info = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None

    # Extract video stream info
    width = 0
    height = 0
    codec = None
    rotation = 0
    duration = 0.0
    bitrate = 0
    creation_time = None

    for stream in info.get('streams', []):
        if stream.get('codec_type') == 'video':
            width = int(stream.get('width', 0))
            height = int(stream.get('height', 0))
            codec = stream.get('codec_name')

            for side in stream.get('side_data_list', []):
                if 'rotation' in side:
                    rotation = int(float(side['rotation']))
                    break

            stream_tags = stream.get('tags', {})
            if 'creation_time' in stream_tags:
                creation_time = stream_tags['creation_time']
            break

    # Skip files with no video stream
    if width == 0 or height == 0:
        return None

    # Format info
    fmt = info.get('format', {})
    duration = float(fmt.get('duration', 0))
    bitrate = int(fmt.get('bit_rate', 0))

    # Try format tags for creation_time if not found in stream
    if creation_time is None:
        tags = fmt.get('tags', {})
        if tags and 'creation_time' in tags:
            creation_time = tags['creation_time']

    file_size = path.stat().st_size if path.exists() else 0

    return {
        'path': str(path),
        'filename': path.name,
        'source': 'recovered',
        'creation_time': creation_time,
        'duration': duration,
        'width': width,
        'height': height,
        'rotation': rotation,
        'codec': codec,
        'bitrate': bitrate,
        'size': file_size,
    }


def find_recovered_files(base_dir: Path = None) -> List[Path]:
    """Find all f*_ftyp.mov files in PhotoRec recovery directories."""
    if base_dir is None:
        base_dir = RECOVERY_BASE

    video_files = []
    for rec_dir in sorted(base_dir.glob(RECOVERY_PATTERN)):
        if rec_dir.is_dir():
            for ftyp in rec_dir.glob('f*_ftyp.mov'):
                video_files.append(ftyp)

    return sorted(set(video_files))


def build_inventory(
    base_dir: Path = None,
    output_path: Path = None,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Scan recovered files and build inventory.

    Args:
        base_dir: Base directory containing recup_dir.* folders
        output_path: Where to save the JSON
        show_progress: Show tqdm progress bar

    Returns:
        List of video metadata dicts
    """
    if base_dir is None:
        base_dir = RECOVERY_BASE
    if output_path is None:
        output_path = OUTPUT_PATH

    video_files = find_recovered_files(base_dir)
    logger.info(f"Found {len(video_files)} recovered video files to scan")

    inventory = []
    failed = 0
    no_video = 0

    iterator = video_files
    if show_progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(video_files, desc="Scanning recovered", unit="file")
        except ImportError:
            pass

    for vf in iterator:
        metadata = extract_video_metadata(vf)
        if metadata is not None:
            inventory.append(metadata)
        else:
            failed += 1

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=1)

    logger.info(f"Recovered inventory: {len(inventory)} valid, {failed} skipped/failed")
    logger.info(f"Saved to: {output_path}")

    return inventory


if __name__ == '__main__':
    build_inventory()
