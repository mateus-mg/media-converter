# recovery/ — Squashed File Recovery

**Parent:** [../AGENTS.md](../AGENTS.md)

## OVERVIEW

Recovery tools for detecting and organizing "squashed" video files (files with wrong extensions or duplicate names).

## STRUCTURE

```
recovery/
├── detect_squashed.py      # Find videos with wrong extensions
├── find_pairs.py           # Match original → converted files
├── match_originals.py      # Cross-reference original sources
├── organize.py             # Move squashed to recovery folder
├── run_pipeline.py         # Orchestrate full recovery
├── report.py               # Generate recovery reports
├── inventory_recovered.py  # Catalog recovered files
└── inventory_server.py     # Serve inventory over HTTP
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Detect wrong extension | `detect_squashed.py` | ffprobe-based detection |
| Match pairs | `find_pairs.py` | Filename similarity matching |
| Organize files | `organize.py` | Move to recovery/ folder |
| Full pipeline | `run_pipeline.py` | End-to-end recovery |
| HTTP server | `inventory_server.py` | Browse recovered inventory |

## CONVENTIONS

- **Path objects:** Consistent `pathlib.Path` usage
- **Subprocess:** Heavy use of `ffprobe` for metadata
- **JSON output:** Reports written as structured JSON

## ANTI-PATTERNS

- **WARNING in print:** Uses `print()` not logging in `run_pipeline.py`
- **No tests:** No dedicated recovery/ tests (tests/recovery/ only has `__init__.py`)

## COMMANDS

```bash
# Run full recovery pipeline
python -m scripts.recovery.run_pipeline /path/to/media

# Start inventory server
python -m scripts.recovery.inventory_server
```
