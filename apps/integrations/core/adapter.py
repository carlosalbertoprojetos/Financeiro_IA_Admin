from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from django.utils import timezone

from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.models import IntegrationConnection


@dataclass
class IncrementalFetchResult:
    """Result of an incremental provider fetch."""

    payload: Any
    cursor: dict[str, Any]
    complete: bool = True
    fetched_count: int = 0


class BaseIntegrationAdapter(ABC):
    """
    Abstract adapter contract for external task providers.

    Subclasses implement provider-specific logic; SyncEngine orchestrates
    persistence and events without provider-specific code.
    """

    provider: ClassVar[str]

    @abstractmethod
    def authenticate(self, connection: IntegrationConnection) -> None:
        """Validate credentials and prepare the client session."""

    @abstractmethod
    def fetch(self, connection: IntegrationConnection) -> Any:
        """Fetch raw provider payload (API response, file rows, etc.)."""

    @abstractmethod
    def map(self, raw_payload: Any, connection: IntegrationConnection) -> list[CanonicalTask]:
        """Transform raw payload into canonical tasks."""

    def sync(self, connection: IntegrationConnection) -> list[CanonicalTask]:
        """
        Default sync pipeline: authenticate → fetch → map.

        SyncEngine calls this (or equivalent steps) then persists results.
        Override only when a provider needs custom orchestration.
        """
        self.authenticate(connection)
        raw_payload = self.fetch(connection)
        return self.map(raw_payload, connection)

    def fetch_incremental(
        self,
        state: IngestionCursor,
        connection: IntegrationConnection,
    ) -> IncrementalFetchResult:
        """
        Incremental fetch using the stored cursor.

        Default implementation performs a full fetch and advances the cursor
        timestamp. Providers should override for true delta sync.
        """
        self.authenticate(connection)
        raw_payload = self.fetch(connection)
        synced_at = timezone.now().isoformat()
        return IncrementalFetchResult(
            payload=raw_payload,
            cursor={"since": synced_at, "mode": "full_fallback"},
            complete=True,
            fetched_count=self._count_payload_items(raw_payload),
        )

    def _count_payload_items(self, raw_payload: Any) -> int:
        if isinstance(raw_payload, dict):
            for key in ("cards", "tasks", "items", "issues"):
                items = raw_payload.get(key)
                if isinstance(items, list):
                    return len(items)
        if isinstance(raw_payload, list):
            return len(raw_payload)
        return 0
