"""Webhook Debugger — utility helpers for retry operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def disable_retry(data: Dict[str, Any]) -> Dict[str, Any]:
    """Retry disable — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "response_ms" not in result:
        raise ValueError(f"Retry must include 'response_ms'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["response_ms"]).encode()).hexdigest()[:12]
    return result


def register_retrys(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Retry records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("register_retrys: %d items after filter", len(out))
    return out[:limit]


def retry_retry(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "url" in updated and not isinstance(updated["url"], (int, float)):
        try:
            updated["url"] = float(updated["url"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_retry(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Retry invariants."""
    required = ["response_ms", "url", "event_type"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_retry: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def replay_retry_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk replay."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
