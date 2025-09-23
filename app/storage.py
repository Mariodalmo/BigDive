import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi.encoders import jsonable_encoder


class GroundTruthStore:
    """JSON-backed append-only store for feedback ground truth entries.

    The store maintains a simple JSON array at the configured file path.
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def ensure_initialized(self) -> None:
        """Create parent directories and initialize the JSON file if missing."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            # Initialize with an empty JSON array
            self.file_path.write_text("[]", encoding="utf-8")

    def _read_all(self) -> List[Dict[str, Any]]:
        """Read all entries from the store."""
        try:
            content = self.file_path.read_text(encoding="utf-8")
            data = json.loads(content or "[]")
            if isinstance(data, list):
                return data
            # If somehow corrupted into a non-list, reset to empty list
            return []
        except FileNotFoundError:
            return []

    def _atomic_write(self, data: List[Dict[str, Any]]) -> None:
        """Write using a simple atomic replace strategy."""
        temp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(temp_path, self.file_path)

    def append(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Append an item to the store and return the encoded item stored.

        Datetime and other non-JSON-native types are encoded using FastAPI's
        jsonable_encoder for consistency with API responses.
        """
        self.ensure_initialized()
        encoded_item = jsonable_encoder(item)
        existing = self._read_all()
        existing.append(encoded_item)
        self._atomic_write(existing)
        return encoded_item

