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
from apps.intelligence.services.report_query.engine.analytical_enrichment import (
    build_report_analytical_layer,
)
from apps.intelligence.services.report_query.engine.executive_narrative import (
    build_executive_narrative,
)
from apps.intelligence.services.report_query.engine.discovery_engine import (
    build_discovery_insights,
)
from apps.intelligence.services.report_query.engine.executive_story import (
    build_executive_story,
)
from apps.intelligence.services.report_query.engine.queryset_builder import build_filtered_cards
from apps.intelligence.services.report_query.exporters import export_report
from apps.intelligence.services.report_query.output_contract import build_report_output_contract
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
    analytical = build_report_analytical_layer(
        cards=cards,
        card_rows=card_rows,
        payload=payload,
        report_data=report_data,
        metrics_summary=metrics_summary,
        grouped_summary=grouped,
    )
    executive_narrative = build_executive_narrative(analytical)
    discovery = build_discovery_insights(analytical, executive_narrative)
    executive_story = build_executive_story(
        summary=report_data,
        metrics=analytical.get("metrics_pack", {}),
        analytical_enrichment=analytical,
        executive_narrative=executive_narrative,
        discovery=discovery,
        risks=analytical.get("metrics_pack", {}).get("risks", {}),
        recommendations=analytical.get("recommendations", []),
    )

    result = {
        "meta": {
            "board_id": payload.board_id,
            "report_type": payload.report_type.value,
            "matched_cards": len(cards),
            "returned_cards": len(card_rows),
            "filters": payload.to_cache_key_dict(),
            "cache_hit": cache_hit,
            "report_quality_score": analytical["quality"]["report_quality_score"],
            "report_quality_label": analytical["quality"]["label"],
            "executive_readability_score": executive_narrative["executive_readability_score"]["score"],
            "executive_readability_label": executive_narrative["executive_readability_score"]["label"],
            "report_intelligence_score": discovery["report_intelligence_score"]["score"],
            "report_intelligence_label": discovery["report_intelligence_score"]["label"],
            "executive_story_quality_score": executive_story["executive_story_quality_score"]["score"],
            "executive_story_quality_label": executive_story["executive_story_quality_score"]["label"],
            "metrics_requested": [m.value for m in payload.metrics],
            "group_by": [g.value for g in payload.group_by],
            "sort": {"by": payload.sort_by.value, "order": payload.sort_order.value},
            "limit": payload.limit,
        },
        "data": report_data,
        "metrics": metrics_summary,
        "grouped": grouped,
        "analytical": analytical,
        "executive_narrative": executive_narrative,
        "discovery": discovery,
        "executive_story": executive_story,
        "report_quality_score": analytical["quality"]["report_quality_score"],
        "report_quality_label": analytical["quality"]["label"],
        "executive_readability_score": executive_narrative["executive_readability_score"],
        "report_intelligence_score": discovery["report_intelligence_score"],
        "executive_story_quality_score": executive_story["executive_story_quality_score"],
        "missing_sections": analytical["quality"]["missing_sections"],
        "improvement_suggestions": analytical["quality"]["improvement_suggestions"],
        "cards": card_rows,
    }
    output_contract = build_report_output_contract(result)
    result.update(
        {
            "report_output": output_contract,
            "executive_brief": output_contract["executive_brief"],
            "management_diagnosis": output_contract["management_diagnosis"],
            "analytical_appendix": output_contract["analytical_appendix"],
            "executive_tables": output_contract["executive_tables"],
            "rankings": output_contract["rankings"],
            "commercial_report_score": output_contract["commercial_report_score"],
        }
    )

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
