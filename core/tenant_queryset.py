from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db import models

from core.tenant_context import get_current_tenant_id


class TenantScopedQuerySet(models.QuerySet):
    """QuerySet helpers for models that carry a tenant FK."""

    def for_tenant(self, tenant_or_id):
        tenant_id = getattr(tenant_or_id, "pk", tenant_or_id)
        if tenant_id in (None, ""):
            raise PermissionDenied("Tenant scope is required.")
        return self.filter(tenant_id=tenant_id)


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
    """Manager that honors explicit tenant context when one is active."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            return qs.filter(tenant_id=tenant_id)
        return qs
