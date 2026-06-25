from __future__ import annotations

import os
from typing import Any


DEFAULT_FLAGS: dict[str, bool] = {
    "FEATURE_NEW_EQL_PARSER": False,
    "FEATURE_NEW_SEMANTIC_MAPPER": False,
    "FEATURE_NEW_METRICS_ENGINE": False,
    "FEATURE_QCL_COMPILER": True,
    "FEATURE_SEMANTIC_LAYER": True,
    "FEATURE_CMGL_ENFORCEMENT": True,
    "FEATURE_ODTL_TRACING": True,
}


def _env_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes")


def get_flag(name: str) -> bool:
    default = DEFAULT_FLAGS.get(name, False)
    return _env_bool(name, default)


def all_flags() -> dict[str, bool]:
    return {name: get_flag(name) for name in DEFAULT_FLAGS}


def is_enabled(feature: str) -> bool:
    return get_flag(feature)
