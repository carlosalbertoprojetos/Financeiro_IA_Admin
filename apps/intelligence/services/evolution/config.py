from __future__ import annotations

import os


def is_safe_mode() -> bool:
    return os.environ.get("EOR_SAFE_MODE", "false").lower() in ("true", "1", "yes")
