from __future__ import annotations

from django.core.exceptions import PermissionDenied

from core.models import Tenant
from core.tenant_context import request_tenant_id


def get_request_tenant(request) -> Tenant:
    tenant_id = request_tenant_id(request)
    if tenant_id is None:
        raise PermissionDenied("Tenant scope is required. Send X-Tenant-Id or tenant_id.")
    tenant = Tenant.objects.filter(pk=tenant_id, is_active=True).first()
    if not tenant:
        raise PermissionDenied("Tenant not found or inactive.")
    return tenant


def assert_board_belongs_to_tenant(board_id: str, tenant: Tenant) -> None:
    if not board_id:
        return
    from integrations.trello.models import Board

    if not Board.all_objects.filter(trello_id=board_id, tenant=tenant).exists():
        raise PermissionDenied("Board is not available for the current tenant.")
