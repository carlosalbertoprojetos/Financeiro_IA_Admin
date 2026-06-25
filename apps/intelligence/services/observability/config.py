from __future__ import annotations

import os


def is_debug_mode() -> bool:
    return os.environ.get("EOR_DEBUG_MODE", "false").lower() in ("true", "1", "yes")
