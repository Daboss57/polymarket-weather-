"""Simple file-based JSON caching helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonCache:
    """Naive JSON cache to support reproducible local runs."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, key: str) -> Any | None:
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save(self, key: str, value: Any) -> None:
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(value, indent=2, default=str))
