from __future__ import annotations


ONBOARDING_STEPS = [
    "account",
    "organization",
    "trello_token",
    "connection_test",
    "initial_sync",
    "board_discovery",
    "board_selection",
    "indexing",
    "first_analysis",
    "first_executive_report",
]


def onboarding_blueprint() -> dict[str, object]:
    return {
        "goal": "Time To First Value < 10 minutes",
        "steps": [
            {"step": step, "order": index + 1, "status": "defined"}
            for index, step in enumerate(ONBOARDING_STEPS)
        ],
        "success_event": "first_executive_report_generated",
        "blocking_conditions": [
            "invalid_trello_credentials",
            "no_boards_found",
            "initial_sync_failed",
            "empty_board_selected",
        ],
    }

