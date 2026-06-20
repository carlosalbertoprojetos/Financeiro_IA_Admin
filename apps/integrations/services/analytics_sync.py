from __future__ import annotations

from typing import Any

from django.core.cache import cache

from apps.dashboards.services.canonical_metrics import build_canonical_dashboard
from apps.integrations.models import IntegrationConnection

ANALYTICS_CACHE_TTL = 3600


def analytics_cache_key(provider: str, project_id: str = "") -> str:
    return f"integrations:analytics:{provider}:{project_id or 'all'}"


def refresh_canonical_analytics(
    *,
    provider: str,
    project_id: str = "",
) -> dict[str, Any]:
    """
    Recompute dashboard analytics from canonical tasks and cache the summary.

    Dashboard endpoints read live from CanonicalTaskRecord; the cache supports
    fast worker-side invalidation and monitoring.
    """
    payload = build_canonical_dashboard(
        project_id=project_id or None,
        source_provider=provider,
    )
    summary = payload["summary"]
    cache.set(
        analytics_cache_key(provider, project_id),
        {
            "summary": summary,
            "generated_at": payload["generated_at"],
        },
        timeout=ANALYTICS_CACHE_TTL,
    )
    return summary


def refresh_connection_analytics(connection: IntegrationConnection) -> dict[str, Any]:
    """Refresh analytics for a specific integration connection."""
    summary = refresh_canonical_analytics(
        provider=connection.provider,
        project_id=connection.project_id,
    )
    connection.mark_synced()
    return summary


def get_cached_analytics_summary(
    *,
    provider: str,
    project_id: str = "",
) -> dict[str, Any] | None:
    cached = cache.get(analytics_cache_key(provider, project_id))
    if not cached:
        return None
    return cached.get("summary")
