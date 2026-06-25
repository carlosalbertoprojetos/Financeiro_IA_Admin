from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from django.core.cache import cache

from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload

logger = logging.getLogger(__name__)

CACHE_PREFIX = "eor:report_query:"
DEFAULT_TTL = 3600


def _cache_key(payload: ReportQueryPayload) -> str:
    raw = json.dumps(payload.to_cache_key_dict(), sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return f"{CACHE_PREFIX}{digest}"


def get_cached_report(payload: ReportQueryPayload) -> dict[str, Any] | None:
    key = _cache_key(payload)
    try:
        return cache.get(key)
    except Exception as exc:
        logger.debug("Cache get skipped: %s", exc)
        return None


def set_cached_report(payload: ReportQueryPayload, result: dict[str, Any], ttl: int = DEFAULT_TTL) -> None:
    key = _cache_key(payload)
    try:
        cache.set(key, result, ttl)
    except Exception as exc:
        logger.debug("Cache set skipped: %s", exc)


def invalidate_board_cache(board_id: str) -> None:
    """Best-effort cache invalidation — pattern delete when supported."""
    try:
        cache.delete_pattern(f"{CACHE_PREFIX}*")  # type: ignore[attr-defined]
    except AttributeError:
        logger.debug("Cache backend does not support delete_pattern")
