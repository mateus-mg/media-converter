#!/usr/bin/env python3
"""
Recovery Pipeline - Orchestrate the full video recovery process

Runs all stages in sequence:
    1. Inventory server (Ellen + Mateus)
    2. Inventory recovered (PhotoRec)
    3. Find pairs (Ellen <-> Mateus)
    4. Detect squashed
    5. Match originals
    6. Organize
    7. Report

Usage:
    python3 scripts/recovery/run_pipeline.py [--skip-inventory] [--dry-run-organize]
"""

import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from recovery.inventory_server import build_inventory as build_server_inventory
from recovery.inventory_recovered import build_inventory as build_recovered_inventory
from recovery.find_pairs import main as find_pairs
from recovery.detect_squashed import main as detect_squashed
from recovery.match_originals import main as match_originals
from recovery.organize import organize_pairs
from recovery.report import generate_report


def run_pipeline(skip_inventory: bool = False, dry_run_organize: bool = False):
    """Run the full recovery pipeline."""
    start = time.time()
    data_dir = Path(__file__).parent.parent.parent / 'data'

    print("\n" + "=" * 60)
    print("VIDEO RECOVERY PIPELINE FOR ASPECT RATIO BUG")
    print("=" * 60)

    # Stage 1: Server inventory
    if not skip_inventory:
        print("\n>>> STAGE 1: Server inventory (Ellen + Mateus)")
        print("    This may take several minutes...")
        build_server_inventory()
    else:
        print("\n>>> STAGE 1: SKIPPED (using existing inventory)")

    # Stage 2: Recovered inventory
    if not skip_inventory:
        print("\n>>> STAGE 2: Recovered inventory (PhotoRec)")
        print("    This may take several minutes...")
        build_recovered_inventory()
    else:
        print("\n>>> STAGE 2: SKIPPED (using existing inventory)")

    # Stage 3: Find pairs
    print("\n>>> STAGE 3: Find pairs (Ellen <-> Mateus)")
    pairs = find_pairs()
    print(f"    Result: {len(pairs)} pairs found")

    # Stage 4: Detect squashed
    print("\n>>> STAGE 4: Detect squashed videos")
    squashed = detect_squashed()
    print(f"    Result: {len(squashed)} squashed videos detected")

    # Stage 5: Match originals
    print("\n>>> STAGE 5: Match with recovered originals")
    matched = match_originals()
    print(f"    Result: {len(matched)} pairs with original found")

    # Stage 6: Organize (if not dry run)
    if not dry_run_organize:
        print("\n>>> STAGE 6: Organize pairs (MOVE files)")
        print("    WARNING: Squashed files will be MOVED!")
        confirm = input("    Confirm? (y/N): ")
        if confirm.lower() == 'y':
            stats = organize_pairs()
            print(f"    Result: {stats}")
        else:
            print("    Skipping organization")
    else:
        print("\n>>> STAGE 6: DRY RUN - organization")
        stats = organize_pairs(dry_run=True)
        print(f"    Result (simulated): {stats}")

    # Stage 7: Report
    print("\n>>> STAGE 7: Generate report")
    generate_report()

    elapsed = time.time() - start
    print(f"\nPipeline completed in {elapsed:.1f} seconds")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recovery pipeline for squashed videos')
    parser.add_argument('--skip-inventory', action='store_true',
                        help='Skip inventory stages (use existing data)')
    parser.add_argument('--dry-run-organize', action='store_true',
                        help="Don't actually move files")
    args = parser.parse_args()
    run_pipeline(skip_inventory=args.skip_inventory, dry_run_organize=args.dry_run_organize)
