"""Intelligence pipeline orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from apps.intelligence.services.enrichment.engine import enrich_board
from apps.intelligence.services.executive_summary.agent import build_executive_summary
from apps.intelligence.services.knowledge.extractor import extract_board_knowledge
from apps.intelligence.services.operational_score.scorer import compute_operational_score
from apps.intelligence.services.report_builder import build_executive_report
from apps.intelligence.services.timeline.engine import build_timeline_events_for_board
from integrations.trello.models import Board

logger = logging.getLogger(__name__)


def run_intelligence_pipeline(
    board_trello_id: str,
    *,
    use_ai: bool = True,
) -> dict[str, Any]:
    """
    Full intelligence pipeline:
    1. Timeline events
    2. Enrichment
    3. Knowledge extraction
    4. Operational score
    5. Executive report
    """
    board = Board.objects.filter(trello_id=board_trello_id).first()
    if not board:
        return {"error": "Board not found", "board_id": board_trello_id}

    timeline_count = build_timeline_events_for_board(board)
    enrichments = enrich_board(board_trello_id)
    knowledge = extract_board_knowledge(board)
    score = compute_operational_score(board_trello_id=board_trello_id)
    report = build_executive_report(board_trello_id, use_ai=use_ai)

    logger.info(
        "Intelligence pipeline completed for board %s: %s timeline events, %s enrichments",
        board_trello_id,
        timeline_count,
        len(enrichments),
    )

    return {
        "board_id": board_trello_id,
        "timeline_events_created": timeline_count,
        "enrichments_count": len(enrichments),
        "knowledge_entries": len(knowledge),
        "operational_score": {"score": score.score, "level": score.level},
        "report": report,
    }
