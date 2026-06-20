"""Resolve which canonical task records belong to a Trello sync scope."""

from __future__ import annotations

from dataclasses import dataclass

from apps.integrations.core.exceptions import ConnectionNotFoundError
from apps.integrations.models import CanonicalTaskRecord, IntegrationConnection
from apps.integrations.trello.connections import get_account_connection, resolve_trello_connection


@dataclass(frozen=True)
class CanonicalScope:
    connection_id: str | None = None
    project_id: str | None = None
    source_provider: str | None = "trello"

    def task_count(self) -> int:
        return _scoped_queryset(self).count()


def _scoped_queryset(scope: CanonicalScope):
    queryset = CanonicalTaskRecord.objects.all()
    if scope.connection_id:
        queryset = queryset.filter(connection_id=scope.connection_id)
    elif scope.project_id:
        queryset = queryset.filter(project_id=scope.project_id)
    if scope.source_provider:
        queryset = queryset.filter(source_provider=scope.source_provider)
    return queryset


def resolve_canonical_scope(
    *,
    connection_id: str | None = None,
    project_id: str | None = None,
    source_provider: str | None = "trello",
) -> CanonicalScope:
    """
    Prefer connection_id (exact sync target) over project_id (board filter).

    When only connection_id is known, derive project_id from the connection record.
    """
    normalized_connection = (connection_id or "").strip() or None
    normalized_project = (project_id or "").strip() or None

    if normalized_connection:
        try:
            connection = resolve_trello_connection(connection_id=normalized_connection)
            return CanonicalScope(
                connection_id=str(connection.pk),
                project_id=connection.project_id or normalized_project or None,
                source_provider=source_provider,
            )
        except ConnectionNotFoundError:
            pass

    if normalized_project:
        return CanonicalScope(
            project_id=normalized_project,
            source_provider=source_provider,
        )

    try:
        connection = resolve_trello_connection()
        return CanonicalScope(
            connection_id=str(connection.pk),
            project_id=connection.project_id or None,
            source_provider=source_provider,
        )
    except ConnectionNotFoundError:
        account = get_account_connection()
        if account:
            return CanonicalScope(
                connection_id=str(account.pk),
                project_id=account.project_id or None,
                source_provider=source_provider,
            )

    return CanonicalScope(source_provider=source_provider)
