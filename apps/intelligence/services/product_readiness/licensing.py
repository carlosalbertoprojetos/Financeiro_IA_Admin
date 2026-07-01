from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import PermissionDenied


@dataclass(frozen=True)
class PlanDefinition:
    name: str
    boards: int
    users: int
    cards_analyzed: int
    modules: list[str] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)
    exports: bool = False
    marketplace: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "limits": {
                "boards": self.boards,
                "users": self.users,
                "cards_analyzed": self.cards_analyzed,
            },
            "modules": self.modules,
            "connectors": self.connectors,
            "exports": self.exports,
            "marketplace": self.marketplace,
        }


PLANS = [
    PlanDefinition(
        name="starter",
        boards=2,
        users=5,
        cards_analyzed=1000,
        modules=["dashboard", "trello_sync", "executive_report"],
        connectors=["trello"],
        exports=False,
    ),
    PlanDefinition(
        name="professional",
        boards=10,
        users=25,
        cards_analyzed=10000,
        modules=["dashboard", "trello_sync", "report_query", "dal_approval", "value_dashboard"],
        connectors=["trello", "jira", "clickup"],
        exports=True,
    ),
    PlanDefinition(
        name="business",
        boards=50,
        users=100,
        cards_analyzed=100000,
        modules=["all_professional", "pocl", "ole", "bve", "self_diagnostics", "customer_success"],
        connectors=["trello", "jira", "clickup", "asana", "monday", "github_projects"],
        exports=True,
        marketplace=True,
    ),
    PlanDefinition(
        name="enterprise",
        boards=-1,
        users=-1,
        cards_analyzed=-1,
        modules=["all", "sso_ready", "custom_connectors", "advanced_audit", "marketplace"],
        connectors=["all"],
        exports=True,
        marketplace=True,
    ),
]

FEATURE_ALIASES = {
    "dal": "dal_approval",
    "ole": "ole",
    "bve": "bve",
    "executive_reports": "executive_report",
    "marketplace": "marketplace",
    "exports": "exports",
}


def plan_catalog() -> dict[str, object]:
    return {
        "status": "ok",
        "plans": [plan.as_dict() for plan in PLANS],
        "enforcement": {
            "mode": "architecture_ready",
            "runtime_guard_required": False,
            "note": "Plan catalog is enforced by require_plan_feature/check_plan_limits.",
        },
    }


def is_feature_enabled(plan_name: str, feature: str) -> bool:
    plan = next((item for item in PLANS if item.name == plan_name), None)
    if not plan:
        return False
    return "all" in plan.modules or feature in plan.modules or any(
        feature.startswith(prefix.replace("all_", "")) for prefix in plan.modules if prefix.startswith("all_")
    ) or (feature == "exports" and plan.exports) or (feature == "marketplace" and plan.marketplace)


def plan_for_tenant(tenant) -> PlanDefinition:
    plan_name = getattr(tenant, "plan", "starter")
    return next((item for item in PLANS if item.name == plan_name), PLANS[0])


def check_plan_limits(tenant, *, boards: int = 0, cards_analyzed: int = 0, connector: str = "") -> dict[str, Any]:
    plan = plan_for_tenant(tenant)
    violations = []
    if plan.boards >= 0 and boards > plan.boards:
        violations.append({"limit": "boards", "allowed": plan.boards, "actual": boards})
    if plan.cards_analyzed >= 0 and cards_analyzed > plan.cards_analyzed:
        violations.append({"limit": "cards_analyzed", "allowed": plan.cards_analyzed, "actual": cards_analyzed})
    if connector and "all" not in plan.connectors and connector not in plan.connectors:
        violations.append({"limit": "connector", "allowed": plan.connectors, "actual": connector})
    return {"allowed": not violations, "plan": plan.name, "violations": violations}


def require_plan_feature(tenant, feature: str) -> None:
    normalized = FEATURE_ALIASES.get(feature, feature)
    if not is_feature_enabled(getattr(tenant, "plan", "starter"), normalized):
        raise PermissionDenied(
            f"Feature '{feature}' requires plan upgrade. Current plan: {getattr(tenant, 'plan', 'starter')}."
        )
