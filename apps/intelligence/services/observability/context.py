from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.intelligence.services.observability.trace.collector import TraceCollector

_active_collector: ContextVar[TraceCollector | None] = ContextVar("odtl_collector", default=None)


def get_collector() -> TraceCollector | None:
    return _active_collector.get()


def set_collector(collector: TraceCollector | None) -> None:
    _active_collector.set(collector)
