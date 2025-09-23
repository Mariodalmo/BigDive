import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .schemas import DocumentIn, DocumentStored

_lock = threading.Lock()


def _get_db_path() -> str:
    """Resolve the JSON database path from environment or default location."""
    return os.environ.get(
        "KNOWLEDGE_DB_PATH",
        os.path.join(os.getcwd(), "data", "knowledge.json"),
    )


def _ensure_parent_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _read_all(path: str | None = None) -> List[Dict]:
    db_path = path or _get_db_path()
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        # Corrupt or empty file; start fresh
        return []


def _write_all(items: List[Dict], path: str | None = None) -> None:
    db_path = path or _get_db_path()
    _ensure_parent_dir(db_path)
    tmp_path = f"{db_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(items, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, db_path)


def add_documents(documents: List[DocumentIn], path: str | None = None) -> List[DocumentStored]:
    now = datetime.now(timezone.utc).isoformat()
    with _lock:
        existing = _read_all(path)
        to_store: List[Dict] = []
        for doc in documents:
            stored_item: Dict = {
                "id": os.urandom(16).hex(),
                "title": doc.title.strip(),
                "url": str(doc.url),
                "type": doc.type,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
            existing.append(stored_item)
            to_store.append(stored_item)
        _write_all(existing, path)
    return [DocumentStored(**item) for item in to_store]


def list_documents(path: str | None = None) -> List[DocumentStored]:
    with _lock:
        items = _read_all(path)
    return [DocumentStored(**item) for item in items]

