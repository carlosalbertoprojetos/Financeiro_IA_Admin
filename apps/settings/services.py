from typing import Any

from django.conf import settings as django_settings

from ai.openai_models import DEFAULT_OPENAI_MODEL, normalize_openai_model, openai_models_payload
from apps.integrations.core.credentials import decrypt_value, encrypt_value
from apps.integrations.models import IntegrationConnection
from apps.integrations.trello.connections import get_account_connection, status_payload
from apps.settings.models import WorkspaceConfig


def _mask_secret(value: str, visible: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "•" * len(value)
    return f"{'•' * (len(value) - visible)}{value[-visible:]}"


def _openai_configured(config: WorkspaceConfig) -> bool:
    if config.openai_api_key:
        return True
    return bool(getattr(django_settings, "OPENAI_API_KEY", ""))


def _openai_model(config: WorkspaceConfig) -> str:
    return config.openai_model or getattr(django_settings, "OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def _resolve_openai_key_display(config: WorkspaceConfig) -> str:
    if config.openai_api_key:
        try:
            return decrypt_value(config.openai_api_key)
        except ValueError:
            return ""
    return getattr(django_settings, "OPENAI_API_KEY", "") or ""


def _trello_section() -> dict[str, Any]:
    connection = get_account_connection()
    if not connection:
        connection = (
            IntegrationConnection.objects.filter(
                provider=IntegrationConnection.Provider.TRELLO,
                is_active=True,
            )
            .order_by("-updated_at")
            .first()
        )

    if not connection:
        return {
            "id": "trello",
            "label": "Trello API",
            "status": "not_configured",
            "configured": False,
            "summary": "Não configurado",
            "connection_id": None,
            "board_id": None,
            "member_username": None,
        }

    payload = status_payload(connection)
    return {
        "id": "trello",
        "label": "Trello API",
        "status": payload.get("status", "disconnected"),
        "configured": payload.get("credentials_configured", False),
        "summary": (
            f"Conectado como {payload['member']['username']}"
            if payload.get("member", {}).get("username")
            else "Credenciais salvas"
        ),
        "connection_id": payload.get("connection_id"),
        "board_id": payload.get("project_id"),
        "member_username": payload.get("member", {}).get("username"),
        "last_synced_at": payload.get("last_synced_at"),
    }


def build_settings_overview() -> dict[str, Any]:
    config = WorkspaceConfig.load()
    openai_from_env = bool(getattr(django_settings, "OPENAI_API_KEY", ""))
    openai_from_db = bool(config.openai_api_key)

    return {
        "module": "settings",
        "status": "active",
        "sections": {
            "workspace": {
                "id": "workspace",
                "label": "Workspace",
                "status": "configured" if config.workspace_name else "empty",
                "workspace_name": config.workspace_name,
                "timezone": config.timezone,
                "editable": True,
            },
            "trello": _trello_section(),
            "openai": {
                "id": "openai",
                "label": "OpenAI",
                "status": "configured" if _openai_configured(config) else "not_configured",
                "configured": _openai_configured(config),
                "source": "database" if openai_from_db else ("environment" if openai_from_env else "none"),
                "model": _openai_model(config),
                "default_model": DEFAULT_OPENAI_MODEL,
                "available_models": openai_models_payload(),
                "api_key_masked": _mask_secret(_resolve_openai_key_display(config)),
                "editable": True,
            },
        },
    }


def update_workspace(*, workspace_name: str) -> WorkspaceConfig:
    config = WorkspaceConfig.load()
    config.workspace_name = workspace_name.strip()
    config.save(update_fields=["workspace_name", "updated_at"])
    return config


def update_openai(*, api_key: str | None = None, model: str | None = None) -> WorkspaceConfig:
    config = WorkspaceConfig.load()
    if api_key is not None:
        stripped = api_key.strip()
        config.openai_api_key = encrypt_value(stripped) if stripped else ""
    if model is not None:
        try:
            config.openai_model = normalize_openai_model(model)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
    config.save(update_fields=["openai_api_key", "openai_model", "updated_at"])
    return config
