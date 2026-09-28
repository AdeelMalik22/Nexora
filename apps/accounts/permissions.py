from uuid import UUID

from django.db import connection
from rest_framework.permissions import BasePermission

from apps.common.context import set_tenant_context

from .models import ShopMembership


def resolve_tenant(request):
    raw_shop_id = request.headers.get("X-Shop-ID")
    if not raw_shop_id:
        return False
    try:
        shop_id = UUID(raw_shop_id)
    except ValueError:
        return False
    membership = ShopMembership.objects.unscoped().select_related("shop", "role").filter(
        user=request.user, shop_id=shop_id, is_active=True
    ).first()
    if membership is None:
        return False
    tokens = set_tenant_context(shop_id)
    request.shop = membership.shop
    request.membership = membership
    request._request.shop = membership.shop
    request._request.membership = membership
    request._request._tenant_context_tokens = tokens
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('nexora.shop_id', %s, false)", [str(shop_id)])
    return True


class TenantContextPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and resolve_tenant(request)


class HasShopPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        if not request.user.is_authenticated or not resolve_tenant(request):
            return False
        membership = getattr(request, "membership", None)
        if membership is None or not membership.is_active:
            return False
        if membership.is_owner or request.user.is_superuser:
            return True
        permission_name = getattr(view, "required_permission", self.required_permission)
        if not permission_name:
            return True
        return membership.role.permissions.filter(codename=permission_name).exists()
