#!/usr/bin/env python3
"""
Recovery Pipeline - Orchestrate the full recovery process

Runs all stages in sequence:
1. Inventory server (Ellen + Mateus)
2. Inventory recovered (PhotoRec)
3. Find pairs (Ellen <-> Mateus)
4. Detect squashed
5. Match originals
6. Report

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
    print("PIPELINE DE RECUPERACAO DE VIDEOS COM BUG DE ASPECT RATIO")
    print("=" * 60)

    # Stage 1: Server inventory
    if not skip_inventory:
        print("\n>>> ESTAGIO 1: Inventario do servidor (Ellen + Mateus)")
        print("    Isso pode levar varios minutos...")
        build_server_inventory()
    else:
        print("\n>>> ESTAGIO 1: SKIPPED (usando inventario existente)")

    # Stage 2: Recovered inventory
    if not skip_inventory:
        print("\n>>> ESTAGIO 2: Inventario recuperado (PhotoRec)")
        print("    Isso pode levar varios minutos...")
        build_recovered_inventory()
    else:
        print("\n>>> ESTAGIO 2: SKIPPED (usando inventario existente)")

    # Stage 3: Find pairs
    print("\n>>> ESTAGIO 3: Encontrar pares (Ellen <-> Mateus)")
    pairs = find_pairs()
    print(f"    Resultado: {len(pairs)} pares encontrados")

    # Stage 4: Detect squashed
    print("\n>>> ESTAGIO 4: Detectar videos squashed")
    squashed = detect_squashed()
    print(f"    Resultado: {len(squashed)} videos squashed detectados")

    # Stage 5: Match originals
    print("\n>>> ESTAGIO 5: Match com originais recuperados")
    matched = match_originals()
    print(f"    Resultado: {len(matched)} pares com original encontrado")

    # Stage 6: Organize (if not dry run)
    if not dry_run_organize:
        print("\n>>> ESTAGIO 6: Organizar pares (MOVER arquivos)")
        print("    ATENCAO: Os arquivos squashed serao MOVIDOS!")
        confirm = input("    Confirmar? (s/N): ")
        if confirm.lower() == 's':
            stats = organize_pairs()
            print(f"    Resultado: {stats}")
        else:
            print("    Pulando organizacao")
    else:
        print("\n>>> ESTAGIO 6: DRY RUN - organizacao")
        stats = organize_pairs(dry_run=True)
        print(f"    Resultado (simulado): {stats}")

    # Stage 7: Report
    print("\n>>> ESTAGIO 7: Gerar relatorio")
    generate_report()

    elapsed = time.time() - start
    print(f"\nPipeline concluido em {elapsed:.1f} segundos")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recovery pipeline for squashed videos')
    parser.add_argument('--skip-inventory', action='store_true',
                        help='Skip inventory stages (use existing data)')
    parser.add_argument('--dry-run-organize', action='store_true',
                        help="Don't actually move files")
    args = parser.parse_args()
    run_pipeline(skip_inventory=args.skip_inventory, dry_run_organize=args.dry_run_organize)
