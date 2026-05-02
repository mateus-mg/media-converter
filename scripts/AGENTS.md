# scripts/ — Core Modules

**Parent:** [../AGENTS.md](../AGENTS.md)

## OVERVIEW

Core Python modules for media conversion. All modules use flexible imports (relative → absolute fallback).

## STRUCTURE

```
scripts/
├── media_converter.py      # 2572 lines — conversion engine
├── cli_manager.py          # 499 lines — Rich interactive CLI
├── config.py               # 249 lines — Singleton config (.env)
├── conversion_db.py        # 124 lines — JSON deduplication
├── interactive_helpers.py  # 234 lines — Prompt utilities
├── log_config.py           # 289 lines — Centralized logging
├── log_formatter.py        # 568 lines — Structured formatting
└── recovery/               # Recovery subpackage (separate AGENTS.md)
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Video encode | `media_converter.py:1158-1500` | FFmpeg command building |
| Image convert | `media_converter.py:722-868` | Pillow → ImageMagick fallback |
| Hardware detect | `media_converter.py:77-163` | NVENC/QSV probing |
| HDR detection | `media_converter.py:166-193` | bt2020 + PQ/HLG check |
| Interactive menu | `cli_manager.py:72-125` | Rich menu loop |
| Config values | `config.py:26-60` | DEFAULTS dict |
| Log formatting | `log_formatter.py` | Section headers, progress |

## CONVENTIONS

- **Dataclasses:** `NvidiaGPU`, `IntelGPU`, `HardwareInfo` for structured data
- **Type hints:** Function signatures throughout
- **Fallbacks:** Try `send2trash` → `gio trash` → `trash-put` → `unlink()`
- **CRITICAL markers:** Safety-critical sections (in-place prevention)

## ANTI-PATTERNS

- **No Protocol/ABC:** Despite clear interfaces, no abstract base classes
- **No mypy:** Type hints not enforced
- **Large file:** `media_converter.py` bundles conversion + hardware + video logic

## COMMANDS

```bash
# Direct module execution
python scripts/media_converter.py /path/to/media
python scripts/cli_manager.py interactive
```
