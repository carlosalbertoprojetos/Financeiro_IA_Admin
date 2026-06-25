from __future__ import annotations

from typing import Any

from apps.intelligence.services.observability.context import get_collector


def record_execution_step(name: str, layer: str, **details: Any) -> None:
    collector = get_collector()
    if collector:
        collector.end_step(name, layer, **details)


def record_filter_applied(field: str, spec: dict[str, Any], matched: int) -> None:
    collector = get_collector()
    if collector:
        collector.record_transformation("filter_applied", field, str(spec), matched=matched)
        collector.record_rule(f"filter:{field}", "query_engine", f"matched {matched} cards")


def record_grouping(dimensions: list[str], groups: int) -> None:
    collector = get_collector()
    if collector:
        collector.record_transformation("group_by", str(dimensions), f"{groups} groups", groups=groups)


def record_sorting(field: str, order: str) -> None:
    collector = get_collector()
    if collector:
        collector.record_transformation("sort", field, order)


def record_cache_event(hit: bool, key: str = "") -> None:
    collector = get_collector()
    if collector:
        collector.record_rule("cache", "query_engine", "hit" if hit else "miss", key=key[:32])


def record_optimization(notes: list[str]) -> None:
    collector = get_collector()
    if collector:
        for note in notes:
            collector.record_rule(note, "optimizer", "applied")


def record_governance(governance: dict[str, Any]) -> None:
    collector = get_collector()
    if collector:
        collector.record_rule("cmgl_governance", "core_model", "validated", governed=governance.get("governed"))


def start_step(name: str, layer: str) -> None:
    collector = get_collector()
    if collector:
        collector.start_step(name, layer)
