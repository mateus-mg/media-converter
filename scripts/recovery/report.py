#!/usr/bin/env python3
"""
Report - Generate final recovery report

Generates a summary report of the recovery pipeline results.

Inputs: data/*.json
Output: data/recovery_report.txt
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / 'data'


def count_by_source(inventory: list) -> Dict[str, int]:
    sources = {}
    for item in inventory:
        src = item.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    return sources


def count_by_confidence(items: list) -> Dict[str, int]:
    confs = {}
    for item in items:
        c = item.get('confidence', 'unknown')
        confs[c] = confs.get(c, 0) + 1
    return confs


def generate_report(data_dir: Path = None) -> str:
    if data_dir is None:
        data_dir = DATA_DIR

    lines = []
    lines.append("=" * 60)
    lines.append("RELATORIO DE RECUPERACAO DE VIDEOS COM BUG DE ASPECT RATIO")
    lines.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    # Server inventory
    inv_path = data_dir / 'inventory_server.json'
    if inv_path.exists():
        inventory = json.load(open(inv_path))
        sources = count_by_source(inventory)
        lines.append(f"\n--- INVENTARIO DO SERVIDOR ---")
        lines.append(f"Total de videos: {len(inventory)}")
        for src, count in sorted(sources.items()):
            lines.append(f"  {src}: {count}")
    else:
        lines.append(f"\n[!] Inventario do servidor nao encontrado")

    # Recovered inventory
    rec_path = data_dir / 'inventory_recovered.json'
    if rec_path.exists():
        recovered = json.load(open(rec_path))
        valid = sum(1 for r in recovered if r.get('width', 0) > 0)
        lines.append(f"\n--- INVENTARIO RECUPERADO (PhotoRec) ---")
        lines.append(f"Arquivos validos com video: {valid}")
    else:
        lines.append(f"\n[!] Inventario recuperado nao encontrado")

    # Pairs
    pairs_path = data_dir / 'duplicate_candidates.json'
    if pairs_path.exists():
        pairs = json.load(open(pairs_path))
        lines.append(f"\n--- PARES ENCONTRADOS (Ellen <-> Mateus) ---")
        lines.append(f"Pares com mesmo creation_time: {len(pairs)}")
    else:
        lines.append(f"\n[!] Pares nao encontrados")

    # Squashed detected
    sq_path = data_dir / 'squashed_detected.json'
    if sq_path.exists():
        squashed = json.load(open(sq_path))
        confs = count_by_confidence(squashed)
        lines.append(f"\n--- VIDEOS SQUASHED DETECTADOS ---")
        lines.append(f"Total: {len(squashed)}")
        for c, count in sorted(confs.items()):
            lines.append(f"  Confianca {c}: {count}")
    else:
        lines.append(f"\n[!] Squashed nao detectados")

    # Matched
    match_path = data_dir / 'matched_with_originals.json'
    if match_path.exists():
        matched = json.load(open(match_path))
        confs = count_by_confidence(matched)
        lines.append(f"\n--- MATCH COM ORIGINAIS RECUPERADOS ---")
        lines.append(f"Pares com original encontrado: {len(matched)}")
        for c, count in sorted(confs.items()):
            lines.append(f"  Confianca {c}: {count}")
    else:
        lines.append(f"\n[!] Match nao realizado")

    # Unmatched
    unmatched_sq_path = data_dir / 'unmatched_squashed.json'
    unmatched_rec_path = data_dir / 'unmatched_recovered.json'
    if unmatched_sq_path.exists():
        unmatched_sq = json.load(open(unmatched_sq_path))
        lines.append(f"\nSquashed sem original recuperado: {len(unmatched_sq)}")
    if unmatched_rec_path.exists():
        unmatched_rec = json.load(open(unmatched_rec_path))
        lines.append(f"Recuperados sem par squashed: {len(unmatched_rec)}")

    lines.append("\n" + "=" * 60)
    lines.append("FIM DO RELATORIO")
    lines.append("=" * 60)

    report = '\n'.join(lines)
    print(report)

    # Save
    report_path = data_dir / 'recovery_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Report saved to: {report_path}")

    return report


if __name__ == '__main__':
    generate_report()
