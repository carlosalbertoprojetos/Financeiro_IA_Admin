from apps.integrations.core.adapter import BaseIntegrationAdapter, IncrementalFetchResult
from apps.integrations.core.canonical import CanonicalTask
from apps.integrations.core.exceptions import ProviderNotReadyError
from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.core.registry import registry
from apps.integrations.models import IntegrationConnection


@registry.register
class GitHubProjectsAdapter(BaseIntegrationAdapter):
    """GitHub Projects provider placeholder for the connector framework."""

    provider = "github_projects"

    def authenticate(self, connection: IntegrationConnection) -> None:
        raise ProviderNotReadyError("GitHub Projects integration is not yet implemented.")

    def fetch(self, connection: IntegrationConnection):
        raise ProviderNotReadyError("GitHub Projects integration is not yet implemented.")

    def map(self, raw_payload, connection: IntegrationConnection) -> list[CanonicalTask]:
        raise ProviderNotReadyError("GitHub Projects integration is not yet implemented.")

    def fetch_incremental(
        self,
        state: IngestionCursor,
        connection: IntegrationConnection,
    ) -> IncrementalFetchResult:
        raise ProviderNotReadyError("GitHub Projects integration is not yet implemented.")

