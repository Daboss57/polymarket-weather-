"""Small HTTP helper with requests-first, urllib fallback."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None


class HttpError(RuntimeError):
    """Raised when HTTP fetch fails."""


def get_json(url: str, params: dict[str, Any], timeout_seconds: int) -> Any:
    """Fetch JSON from an HTTP endpoint with query parameters."""
    if requests is not None:
        try:
            resp = requests.get(url, params=params, timeout=timeout_seconds)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            raise HttpError(str(exc)) from exc

    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}" if query else url
    try:
        with urllib.request.urlopen(full_url, timeout=timeout_seconds) as response:  # nosec B310
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HttpError(str(exc)) from exc
