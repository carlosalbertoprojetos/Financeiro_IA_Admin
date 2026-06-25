from __future__ import annotations

from typing import Any

from apps.intelligence.services.observability.context import get_collector


def trace_ai_interaction(
    *,
    component: str,
    prompt_summary: str,
    context_keys: list[str],
    output_summary: str,
    post_processing: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record AI decision trace — input, context, output (no raw prompts in prod)."""
    collector = get_collector()
    if not collector:
        return
    entry = {
        "component": component,
        "prompt_summary": prompt_summary[:500],
        "context_keys": context_keys,
        "output_summary": output_summary[:500],
        "post_processing": post_processing,
        "metadata": metadata or {},
    }
    collector.trace.ai_decisions.append(entry)


def trace_recommendations(recommendations: list[str], source: str = "domain_intelligence") -> None:
    collector = get_collector()
    if collector:
        trace_ai_interaction(
            component=source,
            prompt_summary="structured operational data",
            context_keys=["entities", "business_metrics", "risks"],
            output_summary="; ".join(recommendations[:5]),
            post_processing="merged_into_recommendations",
        )
