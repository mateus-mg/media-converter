#!/usr/bin/env python3
"""
Detect Squashed - Identify which videos in pairs have wrong aspect ratio

Analyzes pairs (Ellen↔Mateus) and identifies which one is "squashed"
(has wrong aspect ratio due to the bug).

Input: data/duplicate_candidates.json
Output: data/squashed_detected.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

INPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'duplicate_candidates.json'
OUTPUT_PATH = Path(__file__).parent.parent.parent / 'data' / 'squashed_detected.json'

ASPECT_DIFF_THRESHOLD = 0.1


def get_effective_aspect(width: int, height: int, rotation: int) -> float:
    """Calculate effective aspect ratio considering rotation."""
    if abs(rotation) in (90, 270):
        w, h = height, width
    else:
        w, h = width, height
    return w / h if h else 0.0


def detect_squashed_in_pair(pair: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze a pair and identify which video is squashed.

    Returns dict with squashed/correct info, or None if no anomaly detected.
    """
    ellen = pair['ellen']
    mateus = pair['mateus']

    ellen_aspect = get_effective_aspect(
        ellen['width'], ellen['height'], ellen.get('rotation', 0))
    mateus_aspect = get_effective_aspect(
        mateus['width'], mateus['height'], mateus.get('rotation', 0))

    # Determine orientation
    ellen_portrait = ellen['height'] > ellen['width']
    mateus_portrait = mateus['height'] > mateus['width']

    squashed = None
    correct = None
    reason = None
    confidence = 'low'

    # Case 1: One portrait, one landscape → clear anomaly
    if ellen_portrait and not mateus_portrait:
        squashed = mateus
        correct = ellen
        reason = 'ellen_portrait_mateus_landscape'
        confidence = 'high'
    elif not ellen_portrait and mateus_portrait:
        squashed = ellen
        correct = mateus
        reason = 'mateus_portrait_ellen_landscape'
        confidence = 'high'

    # Case 2: Same orientation but different aspect ratios
    if squashed is None:
        aspect_diff = abs(ellen_aspect - mateus_aspect)
        if aspect_diff > ASPECT_DIFF_THRESHOLD:
            # Use rotation as tiebreaker: video WITH rotation metadata is likely correct
            ellen_rotation = ellen.get('rotation', 0)
            mateus_rotation = mateus.get('rotation', 0)

            if ellen_rotation != 0 and mateus_rotation == 0:
                squashed = mateus
                correct = ellen
                reason = f'aspect_diff_{aspect_diff:.3f}_mateus_no_rotation'
                confidence = 'medium'
            elif mateus_rotation != 0 and ellen_rotation == 0:
                squashed = ellen
                correct = mateus
                reason = f'aspect_diff_{aspect_diff:.3f}_ellen_no_rotation'
                confidence = 'medium'
            else:
                # Both have rotation or neither - can't determine automatically
                reason = f'aspect_diff_{aspect_diff:.3f}_inconclusive'
                confidence = 'low'
                # Default: consider the one with smaller file as potentially lower quality
                if ellen['size'] < mateus['size']:
                    squashed = ellen
                    correct = mateus
                else:
                    squashed = mateus
                    correct = ellen

    if squashed is None:
        return None

    return {
        'creation_time': pair.get('creation_time'),
        'reason': reason,
        'confidence': confidence,
        'squashed': squashed,
        'correct': correct,
        'ellen_effective_aspect': round(ellen_aspect, 4),
        'mateus_effective_aspect': round(mateus_aspect, 4),
        'duration_diff': pair.get('duration_diff', 0),
    }


def main(input_path: Path = None, output_path: Path = None) -> List[Dict[str, Any]]:
    """Load pairs, detect squashed, save results."""
    if input_path is None:
        input_path = INPUT_PATH
    if output_path is None:
        output_path = OUTPUT_PATH

    if not input_path.exists():
        logger.error(f"Pairs not found: {input_path}")
        logger.info("Run find_pairs.py first")
        return []

    with open(input_path) as f:
        pairs = json.load(f)

    logger.info(f"Loaded {len(pairs)} pairs")

    results = []
    for pair in pairs:
        result = detect_squashed_in_pair(pair)
        if result is not None:
            results.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)

    # Summary
    high = sum(1 for r in results if r['confidence'] == 'high')
    medium = sum(1 for r in results if r['confidence'] == 'medium')
    low = sum(1 for r in results if r['confidence'] == 'low')

    logger.info(f"Squashed detected: {len(results)} / {len(pairs)} pairs")
    logger.info(f"  High confidence: {high}")
    logger.info(f"  Medium confidence: {medium}")
    logger.info(f"  Low confidence: {low}")
    logger.info(f"Saved to: {output_path}")

    return results


if __name__ == '__main__':
    main()
