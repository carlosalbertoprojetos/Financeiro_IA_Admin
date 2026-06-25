from __future__ import annotations

from enum import Enum
from typing import Any

from apps.intelligence.services.evolution.versioning.core import VERSION_HISTORY, get_layer_versions, get_system_version


class CompatLevel(str, Enum):
    OK = "OK"
    WARN = "WARN"
    BREAK = "BREAK"


# layer -> {from_version: {to_version: level}}
COMPATIBILITY_MATRIX: dict[str, dict[str, dict[str, CompatLevel]]] = {
    "eql": {
        "1.0.0": {"1.0.0": CompatLevel.OK, "1.0.1": CompatLevel.OK, "1.1.0": CompatLevel.WARN, "2.0.0": CompatLevel.BREAK},
        "1.0.1": {"1.0.0": CompatLevel.OK, "1.0.1": CompatLevel.OK, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
        "1.1.0": {"1.0.0": CompatLevel.WARN, "1.0.1": CompatLevel.OK, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
    },
    "query_engine": {
        "1.0.0": {"1.0.0": CompatLevel.OK, "1.0.1": CompatLevel.OK, "1.1.0": CompatLevel.WARN, "2.0.0": CompatLevel.BREAK},
        "1.1.0": {"1.0.0": CompatLevel.WARN, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
    },
    "semantic_layer": {
        "0.9.0": {"0.9.0": CompatLevel.OK, "1.0.0": CompatLevel.WARN, "2.0.0": CompatLevel.BREAK},
        "1.0.0": {"0.9.0": CompatLevel.WARN, "1.0.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
    },
    "cmgl": {
        "1.0.0": {"1.0.0": CompatLevel.OK, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
        "1.1.0": {"1.0.0": CompatLevel.OK, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
    },
    "metrics": {
        "1.0.0": {"1.0.0": CompatLevel.OK, "1.1.0": CompatLevel.WARN, "2.0.0": CompatLevel.BREAK},
        "1.1.0": {"1.0.0": CompatLevel.WARN, "1.1.0": CompatLevel.OK, "2.0.0": CompatLevel.BREAK},
    },
}


def check_layer_compatibility(layer: str, from_version: str, to_version: str) -> CompatLevel:
    """Return compatibility level between two layer versions."""
    layer_matrix = COMPATIBILITY_MATRIX.get(layer, {})
    from_row = layer_matrix.get(from_version, {})
    if to_version in from_row:
        return from_row[to_version]
    if from_version == to_version:
        return CompatLevel.OK
    major_from = from_version.split(".")[0]
    major_to = to_version.split(".")[0]
    if major_from != major_to:
        return CompatLevel.BREAK
    return CompatLevel.WARN


def _layers_for_system(system_version: str) -> dict[str, str]:
    history = VERSION_HISTORY.get(system_version)
    if history:
        return {
            "eql": history["eql"],
            "query_engine": history["query_engine"],
            "semantic_layer": history["semantic_layer"],
            "cmgl": history["cmgl"],
            "metrics": history["metrics"],
        }
    lv = get_layer_versions()
    if system_version in (lv.system, get_system_version()):
        return {
            "eql": lv.eql,
            "query_engine": lv.query_engine,
            "semantic_layer": lv.semantic_layer,
            "cmgl": lv.cmgl,
            "metrics": lv.metrics,
        }
    major = system_version.split(".")[0]
    if major.isdigit() and int(major) >= 2:
        target = f"{major}.0.0"
        return {layer: target for layer in ("eql", "query_engine", "semantic_layer", "cmgl", "metrics")}
    return {
        layer: _map_system_to_layer(system_version, layer)
        for layer in ("eql", "query_engine", "semantic_layer", "cmgl", "metrics")
    }


def check_system_compatibility(from_system: str, to_system: str | None = None) -> dict[str, Any]:
    """Check compatibility across all layers for a system version transition."""
    lv = get_layer_versions()
    to_system = to_system or lv.system
    from_layers = _layers_for_system(from_system)
    to_layers = _layers_for_system(to_system)
    results: dict[str, str] = {}
    worst = CompatLevel.OK
    for name in from_layers:
        fv, tv = from_layers[name], to_layers.get(name, from_layers[name])
        level = check_layer_compatibility(name, fv, tv)
        results[name] = level.value
        if level == CompatLevel.BREAK:
            worst = CompatLevel.BREAK
        elif level == CompatLevel.WARN and worst != CompatLevel.BREAK:
            worst = CompatLevel.WARN
    return {
        "from_system": from_system,
        "to_system": to_system,
        "layers": results,
        "overall": worst.value,
        "compatible": worst != CompatLevel.BREAK,
    }


def _map_system_to_layer(system_version: str, layer: str) -> str:
    mapping = {
        "1.0.0": {"eql": "1.0.0", "query_engine": "1.0.0", "semantic_layer": "0.9.0", "cmgl": "1.0.0", "metrics": "1.0.0"},
        "1.0.1": {"eql": "1.0.1", "query_engine": "1.0.1", "semantic_layer": "1.0.0", "cmgl": "1.0.0", "metrics": "1.0.0"},
    }
    return mapping.get(system_version, {}).get(layer, get_layer_versions().__dict__.get(layer.replace("_layer", "_layer"), "1.0.0"))


def matrix_as_table() -> list[dict[str, Any]]:
    """Export matrix for API/dashboard."""
    rows: list[dict[str, Any]] = []
    for layer, versions in COMPATIBILITY_MATRIX.items():
        for from_v, targets in versions.items():
            for to_v, level in targets.items():
                rows.append({"layer": layer, "from": from_v, "to": to_v, "level": level.value})
    return rows
