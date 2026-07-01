from __future__ import annotations

from django.utils import timezone

from apps.intelligence.models import CustomerOnboardingState


def get_or_create_state(tenant) -> CustomerOnboardingState:
    state, _ = CustomerOnboardingState.objects.get_or_create(tenant=tenant)
    return state


def serialize_state(state: CustomerOnboardingState) -> dict[str, object]:
    return {
        "tenant_id": state.tenant_id,
        "current_step": state.current_step,
        "trello_token_validated": state.trello_token_validated,
        "boards_discovered": state.boards_discovered,
        "boards_selected": state.boards_selected,
        "initial_sync_completed": state.initial_sync_completed,
        "first_report_generated": state.first_report_generated,
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        "errors": state.errors_json,
        "time_to_first_value_seconds": (
            int((state.completed_at - state.created_at).total_seconds())
            if state.completed_at
            else None
        ),
    }


def mark_token_validated(state: CustomerOnboardingState, *, valid: bool, error: str = "") -> CustomerOnboardingState:
    state.trello_token_validated = valid
    state.current_step = CustomerOnboardingState.Step.BOARD_DISCOVERY if valid else CustomerOnboardingState.Step.TRELLO_TOKEN
    if error:
        state.errors_json = [*state.errors_json, {"step": "trello_token", "error": error}]
    state.save()
    return state


def set_discovered_boards(state: CustomerOnboardingState, boards: list[dict]) -> CustomerOnboardingState:
    state.boards_discovered = boards
    state.current_step = CustomerOnboardingState.Step.BOARD_SELECTION
    state.save()
    return state


def select_boards(state: CustomerOnboardingState, board_ids: list[str]) -> CustomerOnboardingState:
    state.boards_selected = board_ids
    state.current_step = CustomerOnboardingState.Step.INDEXING
    state.save()
    return state


def mark_initial_sync(state: CustomerOnboardingState, *, completed: bool, error: str = "") -> CustomerOnboardingState:
    state.initial_sync_completed = completed
    state.current_step = CustomerOnboardingState.Step.FIRST_ANALYSIS if completed else CustomerOnboardingState.Step.INITIAL_SYNC
    if error:
        state.errors_json = [*state.errors_json, {"step": "initial_sync", "error": error}]
    state.save()
    return state


def mark_first_report(state: CustomerOnboardingState) -> CustomerOnboardingState:
    state.first_report_generated = True
    state.current_step = CustomerOnboardingState.Step.COMPLETED
    state.completed_at = timezone.now()
    state.save()
    return state
