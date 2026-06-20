from typing import Type

from apps.integrations.core.adapter import BaseIntegrationAdapter
from apps.integrations.core.exceptions import ProviderNotRegisteredError


class IntegrationRegistry:
    """Maps provider identifiers to adapter classes."""

    def __init__(self) -> None:
        self._adapters: dict[str, type[BaseIntegrationAdapter]] = {}

    def register(self, adapter_cls: type[BaseIntegrationAdapter]) -> type[BaseIntegrationAdapter]:
        provider = adapter_cls.provider
        if not provider:
            raise ValueError(f"Adapter {adapter_cls.__name__} must define provider")
        self._adapters[provider] = adapter_cls
        return adapter_cls

    def get(self, provider: str) -> BaseIntegrationAdapter:
        adapter_cls = self._adapters.get(provider)
        if adapter_cls is None:
            raise ProviderNotRegisteredError(provider)
        return adapter_cls()

    def get_class(self, provider: str) -> type[BaseIntegrationAdapter]:
        adapter_cls = self._adapters.get(provider)
        if adapter_cls is None:
            raise ProviderNotRegisteredError(provider)
        return adapter_cls

    def list_providers(self) -> list[str]:
        return sorted(self._adapters.keys())

    def is_registered(self, provider: str) -> bool:
        return provider in self._adapters


registry = IntegrationRegistry()
