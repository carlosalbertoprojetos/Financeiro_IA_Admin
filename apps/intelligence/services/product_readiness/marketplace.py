from __future__ import annotations


def marketplace_catalog() -> dict[str, object]:
    plugin_types = [
        "kpi",
        "dashboard",
        "connector",
        "exporter",
        "rule",
        "playbook",
    ]
    return {
        "status": "architecture_ready",
        "plugin_types": plugin_types,
        "guardrails": [
            "Plugins must declare tenant scope.",
            "Plugins cannot bypass DAL human approval.",
            "Exporters must use auditable report logs.",
            "Connectors must implement the provider contract without changing EOR core.",
        ],
        "registry_contract": {
            "id": "stable plugin identifier",
            "type": plugin_types,
            "plan_min": "starter|professional|business|enterprise",
            "permissions": "explicit list",
            "entrypoint": "import path or external package id",
        },
    }

