from __future__ import annotations

from datetime import timedelta
from time import perf_counter
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone


def system_health() -> dict[str, Any]:
    checks = [
        _database_check(),
        _redis_check(),
        _cache_check(),
        _queue_check(),
        _scheduler_check(),
        _trello_config_check(),
        _ai_config_check(),
        _storage_check(),
        _workers_check(),
    ]
    status = "ok" if all(check["status"] == "ok" for check in checks) else "degraded"
    if any(check["status"] == "error" for check in checks):
        status = "error"
    return {
        "service": "eor",
        "status": status,
        "timestamp": timezone.now().isoformat(),
        "checks": checks,
    }


def self_diagnostics() -> dict[str, Any]:
    from apps.integrations.models import IngestionQueueEvent, IntegrationConnection
    from integrations.trello.models import Board, Card

    findings = []
    if not getattr(settings, "TRELLO_API_KEY", "") or not getattr(settings, "TRELLO_API_TOKEN", ""):
        findings.append(_finding("tokens_invalid_or_missing", "high", "Trello API key/token not configured."))

    stale_connections = IntegrationConnection.objects.filter(
        is_active=True,
        last_synced_at__lt=timezone.now() - timedelta(hours=24),
    ).count()
    if stale_connections:
        findings.append(_finding("sync_incomplete", "medium", f"{stale_connections} active connections are stale."))

    empty_boards = Board.objects.filter(cards__isnull=True).count()
    if empty_boards:
        findings.append(_finding("board_inconsistent", "medium", f"{empty_boards} boards have no cards."))

    pending_events = IngestionQueueEvent.objects.filter(processed=False).count()
    if pending_events:
        findings.append(_finding("sync_backlog", "medium", f"{pending_events} ingestion events are pending."))

    orphan_cards = Card.objects.filter(board__isnull=True).count()
    if orphan_cards:
        findings.append(_finding("board_inconsistent", "high", f"{orphan_cards} cards have no board."))

    cache_ok = _cache_check()["status"] == "ok"
    if not cache_ok:
        findings.append(_finding("cache_corrupted_or_unavailable", "medium", "Cache read/write health check failed."))

    return {
        "status": "ok" if not findings else "attention_required",
        "findings": findings,
        "recommendations": [finding["recommendation"] for finding in findings],
    }


def multi_tenant_audit() -> dict[str, Any]:
    checks = [
        {
            "area": "data_model",
            "status": "guarded",
            "evidence": "Tenant model exists; Trello Board and IntegrationConnection are tenant-bound. Card/Action inherit scope through Board.",
            "recommendation": "Backfill tenant_id for existing boards before paid pilot.",
        },
        {
            "area": "queries",
            "status": "guarded",
            "evidence": "Paid system APIs require X-Tenant-Id; onboarding board selection rejects cross-tenant boards.",
            "recommendation": "Continue migrating legacy intelligence endpoints to assert_board_belongs_to_tenant.",
        },
        {
            "area": "cache",
            "status": "warning",
            "evidence": "Global cache key prefix exists; product readiness APIs do not cache tenant data.",
            "recommendation": "Prefix all cache keys with tenant_id and board_id.",
        },
        {
            "area": "actions",
            "status": "guarded",
            "evidence": "DAL auto execution is disabled by default and approval flow exists.",
            "recommendation": "Keep human approval mandatory until tenant scoped audit is complete.",
        },
    ]
    return {
        "status": "attention_required" if any(c["status"] == "warning" for c in checks) else "ready",
        "checks": checks,
    }


def _database_check() -> dict[str, str]:
    started = perf_counter()
    try:
        connection.ensure_connection()
        return _probe("database", "ok", started, detail="connection established")
    except Exception as exc:
        return _probe("database", "error", started, error=str(exc), severity="critical")


def _cache_check() -> dict[str, str]:
    started = perf_counter()
    try:
        key = "eor:healthcheck"
        cache.set(key, "ok", timeout=30)
        value = cache.get(key)
        status = "ok" if value == "ok" else "error"
        return _probe("cache", status, started, detail="read/write", severity="high" if status == "error" else "info")
    except Exception as exc:
        return _probe("cache", "error", started, error=str(exc), severity="high")


def _queue_check() -> dict[str, str]:
    started = perf_counter()
    backend = getattr(settings, "INTEGRATION_QUEUE_BACKEND", "local_db")
    return _probe("queues", "ok", started, detail=f"integration backend={backend}")


def _trello_config_check() -> dict[str, str]:
    started = perf_counter()
    configured = bool(getattr(settings, "TRELLO_API_KEY", "") and getattr(settings, "TRELLO_API_TOKEN", ""))
    return _probe(
        "trello",
        "ok" if configured else "warn",
        started,
        detail="credentials configured" if configured else "credentials missing; onboarding cannot connect real boards",
        severity="medium" if not configured else "info",
    )


def _ai_config_check() -> dict[str, str]:
    started = perf_counter()
    configured = bool(getattr(settings, "OPENAI_API_KEY", ""))
    return _probe(
        "ai",
        "ok" if configured else "warn",
        started,
        detail="API key configured" if configured else "AI key missing; no new engine added",
        severity="low" if not configured else "info",
    )


def _storage_check() -> dict[str, str]:
    started = perf_counter()
    static_root = getattr(settings, "STATIC_ROOT", None)
    return _probe("storage", "ok", started, detail=f"static_root={static_root}")


def _workers_check() -> dict[str, str]:
    started = perf_counter()
    broker = getattr(settings, "CELERY_BROKER_URL", "")
    return _probe(
        "workers",
        "ok" if broker else "warn",
        started,
        detail=f"broker={broker or 'not configured'}",
        severity="medium" if not broker else "info",
    )


def _scheduler_check() -> dict[str, str]:
    started = perf_counter()
    enabled = getattr(settings, "CELERY_BEAT_SCHEDULE", None) is not None
    return _probe(
        "scheduler",
        "ok" if enabled else "warn",
        started,
        detail="celery beat schedule configured" if enabled else "no scheduler schedule configured",
        severity="low" if not enabled else "info",
    )


def _redis_check() -> dict[str, str]:
    started = perf_counter()
    redis_url = getattr(settings, "REDIS_CACHE_URL", "")
    return _probe(
        "redis",
        "ok" if redis_url else "warn",
        started,
        detail=redis_url or "REDIS_CACHE_URL not configured; using local cache",
        severity="medium" if not redis_url else "info",
    )


def _probe(name: str, status: str, started: float, *, detail: str = "", error: str = "", severity: str = "info") -> dict[str, str | int | None]:
    return {
        "name": name,
        "status": status,
        "latency_ms": int((perf_counter() - started) * 1000),
        "detail": detail,
        "error": error,
        "last_success_at": timezone.now().isoformat() if status == "ok" else None,
        "severity": severity,
    }


def _finding(code: str, severity: str, evidence: str) -> dict[str, str]:
    recommendations = {
        "tokens_invalid_or_missing": "Run onboarding connection test and save valid Trello credentials.",
        "sync_incomplete": "Trigger incremental sync and inspect failed queue events.",
        "board_inconsistent": "Re-sync board metadata and compare board/list/card counts.",
        "sync_backlog": "Start workers or drain local_db queue.",
        "cache_corrupted_or_unavailable": "Flush cache namespace and verify Redis/cache backend.",
    }
    return {
        "code": code,
        "severity": severity,
        "evidence": evidence,
        "recommendation": recommendations.get(code, "Investigate operational telemetry."),
    }
