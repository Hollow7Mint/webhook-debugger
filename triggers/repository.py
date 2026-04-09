"""Webhook Debugger — Endpoint repository layer."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class WebhookRepository:
    """Endpoint repository for the Webhook Debugger application."""

    def __init__(
        self,
        store: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._store = store
        self._cfg   = config or {}
        self._delivered_at = self._cfg.get("delivered_at", None)
        logger.debug("%s initialised", self.__class__.__name__)

    def disable_endpoint(
        self, delivered_at: Any, response_ms: Any, **extra: Any
    ) -> Dict[str, Any]:
        """Create and persist a new Endpoint record."""
        now = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {
            "id":         str(uuid.uuid4()),
            "delivered_at": delivered_at,
            "response_ms": response_ms,
            "status":     "active",
            "created_at": now,
            **extra,
        }
        saved = self._store.put(record)
        logger.info("disable_endpoint: created %s", saved["id"])
        return saved

    def get_endpoint(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a Endpoint by its *record_id*."""
        record = self._store.get(record_id)
        if record is None:
            logger.debug("get_endpoint: %s not found", record_id)
        return record

    def replay_endpoint(
        self, record_id: str, **changes: Any
    ) -> Dict[str, Any]:
        """Apply *changes* to an existing Endpoint."""
        record = self._store.get(record_id)
        if record is None:
            raise KeyError(f"Endpoint {record_id!r} not found")
        record.update(changes)
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._store.put(record)

    def trigger_endpoint(self, record_id: str) -> bool:
        """Remove a Endpoint; returns True on success."""
        if self._store.get(record_id) is None:
            return False
        self._store.delete(record_id)
        logger.info("trigger_endpoint: removed %s", record_id)
        return True

    def list_endpoints(
        self,
        status: Optional[str] = None,
        limit:  int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return paginated Endpoint records."""
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        results = self._store.find(query, limit=limit, offset=offset)
        logger.debug("list_endpoints: %d results", len(results))
        return results

    def iter_endpoints(
        self, batch_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Yield all Endpoint records in batches of *batch_size*."""
        offset = 0
        while True:
            page = self.list_endpoints(limit=batch_size, offset=offset)
            if not page:
                break
            yield from page
            if len(page) < batch_size:
                break
            offset += batch_size
