from typing import Any

from django.db import transaction

from apps.integrations.core.credentials import decrypt_credentials, encrypt_credentials
from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection
from apps.integrations.trello.client import TrelloClient
from apps.integrations.trello.exceptions import TrelloAPIError

ACCOUNT_PROJECT_ID = ""


def build_credentials(
    api_key: str,
    api_token: str,
    member: dict[str, Any],
) -> dict[str, Any]:
    return {
        "api_key": api_key,
        "api_token": api_token,
        "member_id": member.get("id", ""),
        "member_username": member.get("username") or member.get("fullName") or "",
    }


def save_trello_connection(
    *,
    api_key: str,
    api_token: str,
    member: dict[str, Any],
    board_id: str = "",
    workspace_id: str = "",
    name: str = "",
    board: dict[str, Any] | None = None,
) -> tuple[IntegrationConnection, bool]:
    """Validate and persist a Trello connection with encrypted credentials."""
    project_id = board_id.strip()
    resolved_workspace = workspace_id.strip()
    if board:
        resolved_workspace = resolved_workspace or (board.get("idOrganization") or "")
    resolved_name = name.strip() or (board.get("name") if board else "") or project_id or "Trello"

    credentials = encrypt_credentials(build_credentials(api_key, api_token, member))

    connection, created = IntegrationConnection.objects.update_or_create(
        provider=IntegrationConnection.Provider.TRELLO,
        project_id=project_id,
        defaults={
            "name": resolved_name,
            "workspace_id": resolved_workspace,
            "credentials": credentials,
            "is_active": True,
        },
    )
    return connection, created


def get_account_connection() -> IntegrationConnection | None:
    return (
        IntegrationConnection.objects.filter(
            provider=IntegrationConnection.Provider.TRELLO,
            project_id=ACCOUNT_PROJECT_ID,
            is_active=True,
        )
        .order_by("-updated_at")
        .first()
    )


def resolve_trello_connection(
    *,
    connection_id: str | None = None,
    board_id: str | None = None,
) -> IntegrationConnection:
    if connection_id:
        try:
            return IntegrationConnection.objects.get(
                pk=connection_id,
                provider=IntegrationConnection.Provider.TRELLO,
                is_active=True,
            )
        except IntegrationConnection.DoesNotExist as exc:
            raise ConnectionNotFoundError(connection_id) from exc

    normalized_board = (board_id or "").strip()
    if normalized_board:
        connection = IntegrationConnection.objects.filter(
            provider=IntegrationConnection.Provider.TRELLO,
            project_id=normalized_board,
            is_active=True,
        ).first()
        if connection:
            return connection
        return ensure_board_connection(normalized_board)

    connection = (
        IntegrationConnection.objects.filter(
            provider=IntegrationConnection.Provider.TRELLO,
            is_active=True,
        )
        .exclude(project_id=ACCOUNT_PROJECT_ID)
        .order_by("-updated_at")
        .first()
    )
    if connection:
        return connection

    account = get_account_connection()
    if account:
        raise ConnectionNotFoundError(
            "Trello account connected but no board configured. "
            "Provide board_id on /sync or connect with board_id."
        )

    raise ConnectionNotFoundError("No active Trello connection found")


@transaction.atomic
def ensure_board_connection(board_id: str, workspace_id: str = "") -> IntegrationConnection:
    existing = IntegrationConnection.objects.filter(
        provider=IntegrationConnection.Provider.TRELLO,
        project_id=board_id,
    ).first()
    if existing:
        return existing

    account = get_account_connection()
    if not account:
        raise ConnectionNotFoundError(
            f"No Trello credentials found to sync board {board_id}. Call /connect first."
        )

    creds = decrypt_credentials(account.credentials)
    client = TrelloClient(api_key=creds.get("api_key"), api_token=creds.get("api_token"))
    try:
        board = client.get_board(board_id)
    except TrelloAPIError as exc:
        raise ConnectionNotFoundError(str(exc)) from exc

    connection, _ = save_trello_connection(
        api_key=creds["api_key"],
        api_token=creds["api_token"],
        member={
            "id": creds.get("member_id", ""),
            "username": creds.get("member_username", ""),
        },
        board_id=board_id,
        workspace_id=workspace_id or (board.get("idOrganization") or ""),
        board=board,
    )
    return connection


def status_payload(connection: IntegrationConnection) -> dict[str, Any]:
    creds = decrypt_credentials(connection.credentials)
    tasks_count = CanonicalTaskRecord.objects.filter(connection=connection).count()
    is_account = connection.project_id == ACCOUNT_PROJECT_ID

    return {
        "status": "connected" if connection.is_active else "disconnected",
        "provider": connection.provider,
        "connection_id": str(connection.pk),
        "name": connection.name,
        "project_id": connection.project_id or None,
        "workspace_id": connection.workspace_id or None,
        "is_account_connection": is_account,
        "member": {
            "id": creds.get("member_id", ""),
            "username": creds.get("member_username", ""),
        },
        "last_synced_at": (
            connection.last_synced_at.isoformat() if connection.last_synced_at else None
        ),
        "tasks_count": tasks_count,
        "credentials_configured": bool(creds.get("api_key") and creds.get("api_token")),
    }
