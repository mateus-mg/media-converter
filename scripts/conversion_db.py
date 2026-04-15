"""
JSON-backed conversion database for Media Converter.
Stores a lightweight history of successful conversions.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversionDatabase:
    """Simple JSON database for conversion history."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {"version": 1, "conversions": []}
        self.load()

    def load(self) -> None:
        """Load database contents from disk."""
        if not self.db_path.exists():
            return

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get('conversions'), list):
                self._data = data
        except Exception:
            # Keep the in-memory default if the file is missing or invalid.
            self._data = {"version": 1, "conversions": []}

    def save(self) -> None:
        """Persist database contents to disk atomically."""
        tmp_path = self.db_path.with_suffix(self.db_path.suffix + '.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(self.db_path)

    def _normalize_path(self, path: Path | str) -> str:
        return str(Path(path).resolve())

    def find_record(self, original_path: Path | str) -> Optional[Dict[str, Any]]:
        """Return the most recent record for an original file, if present."""
        normalized = self._normalize_path(original_path)
        for record in reversed(self._data.get('conversions', [])):
            if record.get('original_path') == normalized:
                return record
        return None

    def find_output_path(self, original_path: Path | str) -> Optional[Path]:
        """Return the recorded output path if it still exists."""
        record = self.find_record(original_path)
        if not record:
            return None

        output_path = record.get('output_path')
        if not output_path:
            return None

        path = Path(output_path)
        if path.exists() and path.stat().st_size > 0:
            return path
        return None

    def is_converted(self, original_path: Path | str) -> bool:
        """Check whether a valid converted output already exists."""
        return self.find_output_path(original_path) is not None

    def record_conversion(
        self,
        original_path: Path | str,
        output_path: Path | str,
        *,
        file_type: str,
        codec: Optional[str] = None,
        quality: Optional[str] = None,
        resize: Optional[str] = None,
        image_format: Optional[str] = None,
        source_codec: Optional[str] = None,
        status: str = 'success',
    ) -> Dict[str, Any]:
        """Add or update a conversion record."""
        original = Path(original_path)
        output = Path(output_path)

        record = {
            'original_path': self._normalize_path(original),
            'original_name': original.name,
            'output_path': self._normalize_path(output),
            'output_name': output.name,
            'file_type': file_type,
            'codec': codec,
            'quality': quality,
            'resize': resize,
            'image_format': image_format,
            'source_codec': source_codec,
            'status': status,
            'size_before_bytes': original.stat().st_size if original.exists() else None,
            'size_after_bytes': output.stat().st_size if output.exists() else None,
            'converted_at': datetime.now().isoformat(timespec='seconds'),
        }

        conversions: List[Dict[str, Any]
                          ] = self._data.setdefault('conversions', [])
        conversions[:] = [
            existing for existing in conversions
            if not (
                existing.get('original_path') == record['original_path']
                and existing.get('output_path') == record['output_path']
            )
        ]
        conversions.append(record)
        self._data['updated_at'] = datetime.now().isoformat(timespec='seconds')
        self.save()
        return record

    def all_records(self) -> List[Dict[str, Any]]:
        """Return all records in insertion order."""
        return list(self._data.get('conversions', []))
