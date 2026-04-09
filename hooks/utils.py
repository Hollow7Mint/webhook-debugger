"""Webhook Debugger — utility helpers for webhook operations."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


def inspect_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Webhook inspect — normalises and validates *data*."""
    result = {k: v for k, v in data.items() if v is not None}
    if "delivered_at" not in result:
        raise ValueError(f"Webhook must include 'delivered_at'")
    result["id"] = result.get("id") or hashlib.md5(
        str(result["delivered_at"]).encode()).hexdigest()[:12]
    return result


def register_webhooks(
    items: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Filter and page a sequence of Webhook records."""
    out = [i for i in items if status is None or i.get("status") == status]
    logger.debug("register_webhooks: %d items after filter", len(out))
    return out[:limit]


def replay_webhook(record: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
    """Return a shallow copy of *record* with *overrides* merged in."""
    updated = dict(record)
    updated.update(overrides)
    if "url" in updated and not isinstance(updated["url"], (int, float)):
        try:
            updated["url"] = float(updated["url"])
        except (TypeError, ValueError):
            pass
    return updated


def validate_webhook(record: Dict[str, Any]) -> bool:
    """Return True when *record* satisfies all Webhook invariants."""
    required = ["delivered_at", "url", "event_type"]
    for field in required:
        if field not in record or record[field] is None:
            logger.warning("validate_webhook: missing field %r", field)
            return False
    return isinstance(record.get("id"), str)


def disable_webhook_batch(
    records: List[Dict[str, Any]],
    batch_size: int = 50,
) -> List[List[Dict[str, Any]]]:
    """Slice *records* into chunks of *batch_size* for bulk disable."""
    return [records[i : i + batch_size]
            for i in range(0, len(records), batch_size)]
