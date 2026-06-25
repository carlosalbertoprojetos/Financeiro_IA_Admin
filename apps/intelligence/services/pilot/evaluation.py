from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.intelligence.models import DecisionFeedbackRecord, DecisionRecord


def compute_pilot_metrics(*, board_id: str, since=None) -> dict[str, Any]:
    """POCL success metrics — acceptance rate, efficiency, top risks."""
    fb_qs = DecisionFeedbackRecord.objects.filter(board_id=board_id)
    if since:
        fb_qs = fb_qs.filter(created_at__gte=since)

    accepted = fb_qs.filter(disposition=DecisionFeedbackRecord.Disposition.ACCEPTED).count()
    ignored = fb_qs.filter(disposition=DecisionFeedbackRecord.Disposition.IGNORED).count()
    modified = fb_qs.filter(disposition=DecisionFeedbackRecord.Disposition.MODIFIED).count()
    total_feedback = accepted + ignored + modified

    suggestions_qs = DecisionRecord.objects.filter(board_id=board_id)
    if since:
        suggestions_qs = suggestions_qs.filter(created_at__gte=since)
    suggestions_total = suggestions_qs.count()

    acceptance_rate = round((accepted + modified) / total_feedback * 100, 1) if total_feedback else 0.0

    top_risks = list(
        suggestions_qs.filter(status__in=["OPEN", "PENDING_APPROVAL"])
        .order_by("-score")[:10]
        .values("decision_id", "insight", "priority", "score")
    )

    success_score = _compute_success_score(acceptance_rate, suggestions_total, total_feedback)

    return {
        "board_id": board_id,
        "suggestions_total": suggestions_total,
        "accepted_count": accepted,
        "ignored_count": ignored,
        "modified_count": modified,
        "acceptance_rate_pct": acceptance_rate,
        "top_risks": top_risks,
        "success_score": success_score,
        "pilot_success_threshold_pct": 60,
        "meets_acceptance_target": acceptance_rate >= 60,
    }


def _compute_success_score(acceptance_rate: float, suggestions: int, feedback: int) -> float:
    """Composite pilot score 0-100 based on engagement and acceptance."""
    if suggestions == 0:
        return 0.0
    engagement = min(100, (feedback / max(suggestions, 1)) * 100)
    return round(min(100, acceptance_rate * 0.7 + engagement * 0.3), 1)


def generate_pilot_evaluation_report(*, board_id: str, output_path: str = "") -> str:
    """Full pilot evaluation report for executive review."""
    from pathlib import Path

    metrics = compute_pilot_metrics(board_id=board_id)
    lines = [
        "# Pilot Evaluation Report",
        "",
        f"**Board:** `{board_id}`",
        f"**Generated:** {timezone.now().isoformat()}",
        "",
        "## Success Metrics",
        "",
        f"| Metric | Result | Target | Pass |",
        f"|--------|--------|--------|------|",
        f"| Acceptance rate | {metrics['acceptance_rate_pct']}% | ≥60% | {'✓' if metrics['meets_acceptance_target'] else '✗'} |",
        f"| Suggestions generated | {metrics['suggestions_total']} | — | — |",
        f"| Human feedback recorded | {metrics['accepted_count'] + metrics['ignored_count'] + metrics['modified_count']} | — | — |",
        f"| Pilot success score | {metrics['success_score']}/100 | ≥70 | {'✓' if metrics['success_score'] >= 70 else '✗'} |",
        "",
        "## Verdict",
        "",
    ]

    if metrics["meets_acceptance_target"] and metrics["success_score"] >= 70:
        lines.append("**PILOT ON TRACK** — system is influencing real operational decisions.")
    elif metrics["suggestions_total"] == 0:
        lines.append("**INSUFFICIENT DATA** — activate decision stream and run daily cycle.")
    else:
        lines.append("**NEEDS ATTENTION** — acceptance rate or engagement below target.")

    content = "\n".join(lines)
    path = output_path or "docs/PILOT_EVALUATION_REPORT.md"
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return str(out.resolve())
