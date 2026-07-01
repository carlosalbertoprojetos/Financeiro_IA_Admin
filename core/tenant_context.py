from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from django.core.exceptions import PermissionDenied

_current_tenant_id: ContextVar[int | None] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: int | None) -> None:
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id() -> int | None:
    return _current_tenant_id.get()


@contextmanager
def tenant_scope(tenant_id: int | None) -> Iterator[None]:
    token = _current_tenant_id.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)


def request_tenant_id(request) -> int | None:
    raw = request.headers.get("X-Tenant-Id") or request.query_params.get("tenant_id")
    if raw in (None, "") and hasattr(request, "data"):
        raw = request.data.get("tenant_id")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise PermissionDenied("Invalid tenant_id.") from exc
