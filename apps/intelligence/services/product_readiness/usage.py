from __future__ import annotations

from typing import Any

from django.db.models import Sum


def usage_analytics(board_id: str = "", *, tenant=None) -> dict[str, Any]:
    from apps.integrations.models import CanonicalTaskRecord, IngestionQueueEvent, IntegrationConnection
    from apps.intelligence.models import ActionExecutionLog, BusinessValueRecordModel, DecisionRecord, ReportAuditLog
    from integrations.trello.models import Action, Board, Card

    boards = Board.objects.all()
    cards = Card.objects.all()
    actions = Action.objects.all()
    canonical = CanonicalTaskRecord.objects.all()
    reports = ReportAuditLog.objects.all()
    decisions = DecisionRecord.objects.all()
    executions = ActionExecutionLog.objects.all()
    values = BusinessValueRecordModel.objects.all()
    connections = IntegrationConnection.objects.filter(is_active=True)

    if tenant is not None:
        boards = boards.filter(tenant=tenant)
        connections = connections.filter(tenant=tenant)
        allowed_board_ids = list(boards.values_list("trello_id", flat=True))
        cards = cards.filter(board__tenant=tenant)
        actions = actions.filter(board__tenant=tenant)
        canonical = canonical.filter(connection__tenant=tenant)
        reports = reports.filter(board_id__in=allowed_board_ids)
        decisions = decisions.filter(board_id__in=allowed_board_ids)
        values = values.filter(board_id__in=allowed_board_ids)

    if board_id:
        boards = boards.filter(trello_id=board_id)
        cards = cards.filter(board__trello_id=board_id)
        actions = actions.filter(board__trello_id=board_id)
        canonical = canonical.filter(project_id=board_id)
        reports = reports.filter(board_id=board_id)
        decisions = decisions.filter(board_id=board_id)
        executions = executions.filter(result_json__board_id=board_id)
        values = values.filter(board_id=board_id)

    accepted_statuses = ["EXECUTED", "APPROVED", "SUCCESS"]
    roi = values.aggregate(total=Sum("realized_benefit"), avoided=Sum("avoided_loss"))

    return {
        "board_id": board_id or "all",
        "boards_synced": boards.filter(last_synced_at__isnull=False).count(),
        "cards_analyzed": cards.count() or canonical.count(),
        "events_processed": actions.count() + IngestionQueueEvent.objects.filter(processed=True).count(),
        "reports_generated": reports.count(),
        "actions_suggested": decisions.count(),
        "actions_accepted": executions.filter(status__in=accepted_statuses).count(),
        "roi_generated": {
            "currency": "BRL",
            "realized_benefit": round(roi["total"] or 0, 2),
            "avoided_loss": round(roi["avoided"] or 0, 2),
        },
        "connections": connections.count(),
    }


def customer_success_dashboard(board_id: str = "", *, tenant=None) -> dict[str, Any]:
    usage = usage_analytics(board_id, tenant=tenant)
    total_value = usage["roi_generated"]["realized_benefit"] + usage["roi_generated"]["avoided_loss"]
    return {
        "board_id": usage["board_id"],
        "value_generated_brl": round(total_value, 2),
        "time_saved_hours_estimate": 0,
        "problems_found": usage["actions_suggested"],
        "improvements_suggested": usage["actions_suggested"],
        "operational_maturity": "measurable" if usage["cards_analyzed"] else "not_enough_data",
        "roi": usage["roi_generated"],
        "evidence": [
            "Counts are sourced from persisted EOR records.",
            "Financial value uses BVE records only; no simulated customer metric is mixed into production analytics.",
        ],
    }
