from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from apps.intelligence.models import ReportAuditLog
from apps.intelligence.services.report_query.cache import get_cached_report, set_cached_report
from apps.intelligence.services.report_query.domain.filters import ExportFormat, ReportQueryPayload
from apps.intelligence.services.report_query.engine.post_processor import (
    build_card_rows,
    build_grouped_summary,
    build_metrics_summary,
)
from apps.intelligence.services.report_query.engine.queryset_builder import build_filtered_cards
from apps.intelligence.services.report_query.exporters import export_report
from apps.intelligence.services.report_query.templates.registry import generate_report

logger = logging.getLogger(__name__)


def execute_report_query(payload: ReportQueryPayload) -> dict[str, Any]:
    """Execute a segmented report query with optional cache and audit logging."""
    start = time.perf_counter()
    cache_hit = False

    if payload.use_cache:
        cached = get_cached_report(payload)
        if cached is not None:
            cache_hit = True
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            _audit_log(payload, cached, elapsed_ms, cache_hit=True)
            return {
                **cached,
                "meta": {**cached.get("meta", {}), "cache_hit": True, "processing_ms": elapsed_ms},
            }

    cards, filters_meta = build_filtered_cards(payload)
    report_data = generate_report(
        payload.report_type,
        cards,
        board_id=payload.board_id,
        filters_meta=filters_meta,
    )

    card_rows = build_card_rows(cards, payload)
    metrics_summary = build_metrics_summary(card_rows, payload.metrics)
    grouped = build_grouped_summary(card_rows, payload.group_by) if payload.group_by else {}

    result = {
        "meta": {
            "board_id": payload.board_id,
            "report_type": payload.report_type.value,
            "matched_cards": len(cards),
            "returned_cards": len(card_rows),
            "filters": payload.to_cache_key_dict(),
            "cache_hit": cache_hit,
            "metrics_requested": [m.value for m in payload.metrics],
            "group_by": [g.value for g in payload.group_by],
            "sort": {"by": payload.sort_by.value, "order": payload.sort_order.value},
            "limit": payload.limit,
        },
        "data": report_data,
        "metrics": metrics_summary,
        "grouped": grouped,
        "cards": card_rows,
    }

    export_result = export_report(result, payload.export_format)
    if export_result:
        result["export"] = export_result

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    result["meta"]["processing_ms"] = elapsed_ms

    if payload.use_cache:
        set_cached_report(payload, result)

    _audit_log(payload, result, elapsed_ms, cache_hit=False)
    return result


def _audit_log(
    payload: ReportQueryPayload,
    result: dict[str, Any],
    elapsed_ms: int,
    *,
    cache_hit: bool,
) -> None:
    try:
        ReportAuditLog.objects.create(
            generated_by=payload.generated_by,
            board_id=payload.board_id,
            report_type=payload.report_type.value,
            export_format=payload.export_format.value,
            filters_json=payload.to_cache_key_dict(),
            matched_cards=result.get("meta", {}).get("matched_cards", 0),
            processing_ms=elapsed_ms,
            cache_hit=cache_hit,
            result_summary={
                "report_type": payload.report_type.value,
                "matched_cards": result.get("meta", {}).get("matched_cards", 0),
            },
        )
    except Exception:
        logger.exception("Failed to write report audit log")
