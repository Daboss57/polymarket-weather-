"""Storage/export helpers for analytics artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


def export_json(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, default=str))


def export_csv(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to CSV file; pandas if available else stdlib csv."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if pd is not None:
        pd.DataFrame(records).to_csv(path, index=False)
        return

    if not records:
        path.write_text("")
        return

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def dataclass_list_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    """Convert list of dataclass instances to dictionaries."""
    return [asdict(row) for row in rows]
