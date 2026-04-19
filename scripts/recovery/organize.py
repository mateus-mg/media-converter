#!/usr/bin/env python3
"""
Organize - Move matched pairs to structured recovery directory

Moves squashed videos and their originals to /home/mateus/recuperacao/
Squashed files are MOVED (not copied) from their original location.
Recovered originals are COPIED (since they may match multiple squashed).

Input: data/matched_with_originals.json
Output: /home/mateus/recuperacao/
"""

import csv
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

INPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'matched_with_originals.json'
OUTPUT_DIR = Path('/home/mateus/recuperacao')


def organize_pairs(
    input_path: Path = None,
    output_dir: Path = None,
    dry_run: bool = False,
    min_confidence: str = 'low',
) -> Dict[str, int]:
    """Move matched pairs to recovery directory.

    Args:
        input_path: Path to matched_with_originals.json
        output_dir: Base output directory
        dry_run: If True, don't actually move files
        min_confidence: Minimum confidence to include ('high', 'medium', 'low')

    Returns:
        Stats dict with counts
    """
    if input_path is None:
        input_path = INPUT_PATH
    if output_dir is None:
        output_dir = OUTPUT_DIR

    confidence_order = {'high': 0, 'medium': 1, 'low': 2}
    min_level = confidence_order.get(min_confidence, 2)

    if not input_path.exists():
        logger.error(f"Matched data not found: {input_path}")
        return {}

    with open(input_path) as f:
        matched = json.load(f)

    # Filter by confidence
    filtered = [m for m in matched if confidence_order.get(m.get('confidence', 'low'), 2) <= min_level]
    logger.info(f"Processing {len(filtered)} pairs (confidence >= {min_confidence})")

    # Create output directories
    squashed_dir = output_dir / 'squashed'
    originals_dir = output_dir / 'originals'
    if not dry_run:
        squashed_dir.mkdir(parents=True, exist_ok=True)
        originals_dir.mkdir(parents=True, exist_ok=True)

    stats = {'moved_squashed': 0, 'copied_originals': 0, 'failed': 0, 'skipped': 0}
    csv_rows = []

    for match in filtered:
        squashed_info = match['squashed']
        original_info = match.get('original')
        ct = match.get('creation_time', 'unknown')

        # Sanitize creation_time for filename
        safe_ct = ct.replace(':', '-').replace('T', '_').replace('Z', '') if ct else 'unknown'

        # Move squashed video
        squashed_src = Path(squashed_info['path'])
        squashed_name = f"{safe_ct}_{squashed_src.name}"
        squashed_dst = squashed_dir / squashed_name

        if squashed_src.exists():
            if not dry_run:
                try:
                    shutil.move(str(squashed_src), str(squashed_dst))
                    stats['moved_squashed'] += 1
                except Exception as e:
                    logger.warning(f"Failed to move {squashed_src.name}: {e}")
                    stats['failed'] += 1
                    continue
            else:
                stats['moved_squashed'] += 1
        else:
            logger.warning(f"Squashed file not found: {squashed_src}")
            stats['skipped'] += 1

        # Copy original (don't move - it may be needed for other matches)
        original_src = None
        original_dst = None
        if original_info and Path(original_info['path']).exists():
            original_src = Path(original_info['path'])
            original_name = f"{safe_ct}_{original_src.name}"
            original_dst = originals_dir / original_name

            if not dry_run:
                try:
                    shutil.copy2(str(original_src), str(original_dst))
                    stats['copied_originals'] += 1
                except Exception as e:
                    logger.warning(f"Failed to copy original {original_src.name}: {e}")
                    stats['failed'] += 1
            else:
                stats['copied_originals'] += 1

        # CSV row
        csv_rows.append({
            'squashed_path': squashed_info['path'],
            'original_path': original_info['path'] if original_info else '',
            'correct_path': match.get('correct', {}).get('path', ''),
            'squashed_dimensions': f"{squashed_info['width']}x{squashed_info['height']}",
            'original_dimensions': f"{original_info['width']}x{original_info['height']}" if original_info else '',
            'creation_time': ct,
            'match_confidence': match.get('confidence', ''),
            'match_reason': match.get('reason', ''),
        })

    # Write CSV
    csv_path = output_dir / 'matched_pairs.csv'
    if not dry_run and csv_rows:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_rows[0].keys())
            writer.writeheader()
            writer.writerows(csv_rows)
        logger.info(f"CSV saved to: {csv_path}")

    logger.info(f"Stats: {stats}")
    return stats


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Organize recovery pairs')
    parser.add_argument('--dry-run', action='store_true', help="Don't actually move files")
    parser.add_argument('--min-confidence', choices=['high', 'medium', 'low'],
                        default='low', help='Minimum confidence level')
    args = parser.parse_args()
    organize_pairs(dry_run=args.dry_run, min_confidence=args.min_confidence)
