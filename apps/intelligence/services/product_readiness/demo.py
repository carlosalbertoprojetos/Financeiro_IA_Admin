from __future__ import annotations


def executive_demo_payload() -> dict[str, object]:
    return {
        "mode": "demo",
        "requires_real_token": False,
        "workspace": {
            "organization": "ACME Operations",
            "boards": [
                {"id": "demo-board-sales", "name": "Customer Delivery"},
                {"id": "demo-board-ops", "name": "Operations Control"},
            ],
        },
        "metrics": {
            "boards_synced": 2,
            "cards_analyzed": 128,
            "events_processed": 843,
            "reports_generated": 14,
            "actions_suggested": 37,
            "actions_accepted": 24,
            "roi_generated_brl": 48200,
        },
        "risks": [
            {"title": "SLA breach cluster", "severity": "high", "evidence": "12 cards overdue in Delivery"},
            {"title": "Decision latency", "severity": "medium", "evidence": "Average approval time above 18h"},
        ],
        "value_story": [
            "Identified delay concentration before executive report day.",
            "Prioritized human-approved interventions.",
            "Reduced expected rework by focusing on blocked cards.",
        ],
    }

