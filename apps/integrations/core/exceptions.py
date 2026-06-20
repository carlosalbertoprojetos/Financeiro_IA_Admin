class IntegrationError(Exception):
    """Base error for the integration engine."""


class ProviderNotRegisteredError(IntegrationError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider not registered: {provider}")
        self.provider = provider


class ConnectionNotFoundError(IntegrationError):
    def __init__(self, connection_id: str) -> None:
        super().__init__(f"Integration connection not found: {connection_id}")
        self.connection_id = connection_id


class AuthenticationError(IntegrationError):
    """Raised when provider authentication fails."""


class ProviderNotReadyError(IntegrationError):
    """Raised when a provider adapter is registered but not yet implemented."""
