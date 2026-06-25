from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from apps.intelligence.services.semantic_layer.entities import BusinessEntity, EntityStatus, EntityType


def generate_domain_insights(entities: list[BusinessEntity]) -> list[str]:
    """Generate organizational pattern insights from business entities."""
    if not entities:
        return ["No operational entities in scope for domain analysis."]

    insights: list[str] = []
    total = len(entities)

    category_incidents = Counter(
        e.category for e in entities if e.entity_type == EntityType.INCIDENT
    )
    if category_incidents:
        top_cat, count = category_incidents.most_common(1)[0]
        pct = round(count / max(sum(category_incidents.values()), 1) * 100)
        insights.append(f"{top_cat} accounts for {pct}% of incidents ({count} total)")

    delayed_by_category = Counter(e.category for e in entities if e.status == EntityStatus.DELAYED)
    if delayed_by_category:
        riskiest = delayed_by_category.most_common(1)[0]
        insights.append(f"{riskiest[0]} generates the highest operational delay volume ({riskiest[1]} delayed items)")

    prefix_risk: dict[str, list[float]] = defaultdict(list)
    for e in entities:
        if e.category:
            prefix_risk[e.category].append(e.risk_score)
    if prefix_risk:
        avg_by_prefix = {k: sum(v) / len(v) for k, v in prefix_risk.items() if v}
        if avg_by_prefix:
            top_prefix = max(avg_by_prefix, key=avg_by_prefix.get)  # type: ignore[arg-type]
            insights.append(
                f"Projects with prefix [{top_prefix}] have highest average risk ({avg_by_prefix[top_prefix]:.0f})"
            )

    member_blocks = Counter(
        m for e in entities if e.status == EntityStatus.BLOCKED for m in e.related_members
    )
    if member_blocks:
        top_member, block_count = member_blocks.most_common(1)[0]
        block_pct = round(block_count / max(len([e for e in entities if e.status == EntityStatus.BLOCKED]), 1) * 100)
        insights.append(f"Team member {top_member} concentrates {block_pct}% of blocked items")

    assignee_changes = [
        e for e in entities if "rework" in e.risk_flags or "elevated_risk_score" in e.risk_flags
    ]
    if len(assignee_changes) > total * 0.2:
        insights.append("Incidents increase after assignee changes — review handoff process")

    delivery_failures = Counter(
        e.category for e in entities
        if e.entity_type == EntityType.DELIVERY and e.status in (EntityStatus.DELAYED, EntityStatus.BLOCKED)
    )
    if delivery_failures:
        worst, fail_count = delivery_failures.most_common(1)[0]
        insights.append(f"Delivery type [{worst}] fails most often ({fail_count} failed deliveries)")

    bottlenecks = [e for e in entities if e.entity_type == EntityType.BOTTLENECK]
    if bottlenecks:
        bottleneck_cats = Counter(b.category for b in bottlenecks).most_common(1)
        if bottleneck_cats:
            insights.append(f"Real bottlenecks detected in {bottleneck_cats[0][0]} ({bottleneck_cats[0][1]} items)")

    return insights[:10]
