from __future__ import annotations

from core.tenant_context import set_current_tenant_id


class TenantContextMiddleware:
    """Populate request tenant context from X-Tenant-Id when present."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = request.headers.get("X-Tenant-Id") or request.GET.get("tenant_id")
        try:
            tenant_id = int(raw) if raw not in (None, "") else None
        except (TypeError, ValueError):
            tenant_id = None
        set_current_tenant_id(tenant_id)
        request.tenant_id = tenant_id
        return self.get_response(request)
