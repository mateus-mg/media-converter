#!/usr/bin/env python3
"""
Find Pairs - Match videos between Ellen and Mateus by creation_time

Finds videos that exist in both Ellen and Mateus directories
(same moment in time = same creation_time).

Input: data/inventory_server.json
Output: data/duplicate_candidates.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

INPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'inventory_server.json'
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'duplicate_candidates.json'

# Matching tolerances
CREATION_TIME_TOLERANCE_SEC = 2.0
DURATION_TOLERANCE_SEC = 2.0


def parse_creation_time(ct_str: str) -> float:
    """Parse ISO creation_time to unix-like float for comparison.

    Since we only need relative comparison, we parse to a timestamp.
    """
    if not ct_str:
        return 0.0
    from datetime import datetime
    try:
        # Handle various ISO formats
        ct_str = ct_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(ct_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def find_pairs(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find video pairs between Ellen and Mateus with matching creation_time.

    Returns list of pairs with ellen and mateus video info.
    """
    ellen_videos = []
    mateus_videos = []

    for item in inventory:
        if item.get('source') == 'ellen':
            ellen_videos.append(item)
        elif item.get('source') == 'mateus':
            mateus_videos.append(item)

    logger.info(f"Ellen videos: {len(ellen_videos)}, Mateus videos: {len(mateus_videos)}")

    # Build index by creation_time for efficient matching
    ellen_by_ct = {}
    for v in ellen_videos:
        ct = parse_creation_time(v.get('creation_time', ''))
        if ct > 0:
            if ct not in ellen_by_ct:
                ellen_by_ct[ct] = []
            ellen_by_ct[ct].append(v)

    # Find matching pairs
    pairs = []
    used_ellen = set()
    used_mateus = set()

    for mv in mateus_videos:
        m_ct = parse_creation_time(mv.get('creation_time', ''))
        if m_ct <= 0:
            continue

        # Find closest Ellen match within tolerance
        best_match = None
        best_diff = CREATION_TIME_TOLERANCE_SEC + 1

        for e_ct, e_videos in ellen_by_ct.items():
            diff = abs(e_ct - m_ct)
            if diff < best_diff and diff <= CREATION_TIME_TOLERANCE_SEC:
                for ev in e_videos:
                    if id(ev) not in used_ellen:
                        # Also check duration similarity
                        dur_diff = abs(ev.get('duration', 0) - mv.get('duration', 0))
                        if dur_diff <= DURATION_TOLERANCE_SEC:
                            best_match = ev
                            best_diff = diff

        if best_match is not None:
            pairs.append({
                'creation_time': best_match.get('creation_time'),
                'duration_diff': abs(best_match.get('duration', 0) - mv.get('duration', 0)),
                'time_diff_seconds': best_diff,
                'ellen': best_match,
                'mateus': mv,
            })
            used_ellen.add(id(best_match))
            used_mateus.add(id(mv))

    return pairs


def main(input_path: Path = None, output_path: Path = None) -> List[Dict[str, Any]]:
    """Load inventory, find pairs, save results."""
    if input_path is None:
        input_path = INPUT_PATH
    if output_path is None:
        output_path = OUTPUT_PATH

    if not input_path.exists():
        logger.error(f"Inventory not found: {input_path}")
        logger.info("Run inventory_server.py first")
        return []

    with open(input_path) as f:
        inventory = json.load(f)

    logger.info(f"Loaded {len(inventory)} videos from inventory")

    pairs = find_pairs(inventory)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=1)

    logger.info(f"Found {len(pairs)} pairs")
    logger.info(f"Saved to: {output_path}")

    return pairs


if __name__ == '__main__':
    main()
