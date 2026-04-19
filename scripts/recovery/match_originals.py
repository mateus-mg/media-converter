#!/usr/bin/env python3
"""
Match Originals - Find recovered PhotoRec originals for squashed videos

Matches squashed videos with their original files from the PhotoRec recovery.

Inputs: data/squashed_detected.json, data/inventory_recovered.json
Output: data/matched_with_originals.json
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

SQUASHED_PATH = Path(__file__).parent.parent.parent / 'data' / 'squashed_detected.json'
RECOVERED_PATH = Path(__file__).parent.parent.parent / 'data' / 'inventory_recovered.json'
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'matched_with_originals.json'

CREATION_TIME_TOLERANCE = 2.0
DURATION_TOLERANCE = 1.0


def parse_creation_time(ct_str: str) -> float:
    """Parse ISO creation_time to timestamp float."""
    if not ct_str:
        return 0.0
    from datetime import datetime
    try:
        ct_str = ct_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(ct_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def find_original(squashed: Dict[str, Any], recovered: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the best matching original for a squashed video.

    Matching by creation_time, duration, codec preference.
    """
    s_ct = parse_creation_time(squashed.get('creation_time', ''))
    s_dur = squashed.get('duration', 0)

    if s_ct <= 0:
        return None

    candidates = []
    for rec in recovered:
        r_ct = parse_creation_time(rec.get('creation_time', ''))
        r_dur = rec.get('duration', 0)

        if r_ct <= 0:
            continue

        ct_diff = abs(r_ct - s_ct)
        dur_diff = abs(r_dur - s_dur)

        if ct_diff <= CREATION_TIME_TOLERANCE and dur_diff <= DURATION_TOLERANCE:
            candidates.append(rec)

    if not candidates:
        return None

    # Prefer HEVC (original) over H264 (already converted)
    hevc_candidates = [c for c in candidates if c.get('codec') == 'hevc']
    if hevc_candidates:
        candidates = hevc_candidates

    # If multiple, pick the largest (most complete recovery)
    return max(candidates, key=lambda c: c.get('size', 0))


def main(
    squashed_path: Path = None,
    recovered_path: Path = None,
    output_path: Path = None,
) -> List[Dict[str, Any]]:
    """Match squashed videos with their recovered originals."""
    if squashed_path is None:
        squashed_path = SQUASHED_PATH
    if recovered_path is None:
        recovered_path = RECOVERED_PATH
    if output_path is None:
        output_path = OUTPUT_PATH

    if not squashed_path.exists():
        logger.error(f"Squashed data not found: {squashed_path}")
        return []
    if not recovered_path.exists():
        logger.error(f"Recovered inventory not found: {recovered_path}")
        logger.info("Run inventory_recovered.py first")
        return []

    with open(squashed_path) as f:
        squashed_list = json.load(f)
    with open(recovered_path) as f:
        recovered = json.load(f)

    logger.info(f"Loaded {len(squashed_list)} squashed videos, {len(recovered)} recovered files")

    # Deduplicate: each original can only match one squashed
    used_originals = set()
    matched = []
    unmatched_squashed = []
    unmatched_recovered_paths = set(r['path'] for r in recovered)

    for sq in squashed_list:
        original = find_original(sq['squashed'], recovered)
        if original is not None and original['path'] not in used_originals:
            used_originals.add(original['path'])
            unmatched_recovered_paths.discard(original['path'])
            matched.append({
                'creation_time': sq.get('creation_time'),
                'confidence': sq['confidence'],
                'reason': sq['reason'],
                'squashed': sq['squashed'],
                'correct': sq['correct'],
                'original': original,
                'ellen_effective_aspect': sq.get('ellen_effective_aspect'),
                'mateus_effective_aspect': sq.get('mateus_effective_aspect'),
            })
        else:
            unmatched_squashed.append(sq)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(matched, f, ensure_ascii=False, indent=1)

    # Save unmatched lists
    unmatched_squashed_path = output_path.parent / 'unmatched_squashed.json'
    with open(unmatched_squashed_path, 'w', encoding='utf-8') as f:
        json.dump(unmatched_squashed, f, ensure_ascii=False, indent=1)

    unmatched_recovered = [r for r in recovered if r['path'] in unmatched_recovered_paths]
    unmatched_recovered_path = output_path.parent / 'unmatched_recovered.json'
    with open(unmatched_recovered_path, 'w', encoding='utf-8') as f:
        json.dump(unmatched_recovered, f, ensure_ascii=False, indent=1)

    logger.info(f"Matched: {len(matched)} pairs")
    logger.info(f"Unmatched squashed: {len(unmatched_squashed)}")
    logger.info(f"Unmatched recovered: {len(unmatched_recovered)}")
    logger.info(f"Saved to: {output_path}")

    return matched


if __name__ == '__main__':
    main()
