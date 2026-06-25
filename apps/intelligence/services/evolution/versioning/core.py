from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


SYSTEM_VERSION = "1.0.0"

EQL_VERSION = "1.1.0"
QUERY_ENGINE_VERSION = "1.1.0"
SEMANTIC_LAYER_VERSION = "1.0.0"
CMGL_VERSION = "1.1.0"
METRICS_VERSION = "1.1.0"
ODTL_VERSION = "1.0.0"


@dataclass
class LayerVersions:
    system: str = SYSTEM_VERSION
    eql: str = EQL_VERSION
    query_engine: str = QUERY_ENGINE_VERSION
    semantic_layer: str = SEMANTIC_LAYER_VERSION
    cmgl: str = CMGL_VERSION
    metrics: str = METRICS_VERSION
    odtl: str = ODTL_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "system": self.system,
            "eql": self.eql,
            "query_engine": self.query_engine,
            "semantic_layer": self.semantic_layer,
            "cmgl": self.cmgl,
            "metrics": self.metrics,
            "odtl": self.odtl,
        }


CURRENT_VERSIONS = LayerVersions()

VERSION_HISTORY: dict[str, dict[str, Any]] = {
    "1.0.0": {
        "eql": "1.0.0",
        "query_engine": "1.0.0",
        "semantic_layer": "0.9.0",
        "cmgl": "1.0.0",
        "metrics": "1.0.0",
        "breaking_changes": [],
    },
    "1.0.1": {
        "eql": "1.0.1",
        "query_engine": "1.0.1",
        "semantic_layer": "1.0.0",
        "cmgl": "1.0.0",
        "metrics": "1.0.0",
        "breaking_changes": [],
    },
}


def get_system_version() -> str:
    return os.environ.get("EOR_SYSTEM_VERSION", SYSTEM_VERSION)


def get_layer_versions() -> LayerVersions:
    return CURRENT_VERSIONS


def version_snapshot() -> dict[str, Any]:
    lv = get_layer_versions()
    return {"system_version": get_system_version(), "layers": lv.to_dict()}
