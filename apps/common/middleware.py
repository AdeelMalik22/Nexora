from uuid import UUID

from django.http import JsonResponse

from apps.accounts.models import ShopMembership
from django.db import connection

from .context import clear_tenant_context, set_tenant_context


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        raw_shop_id = request.headers.get("X-Shop-ID")
        if not raw_shop_id:
            return JsonResponse({"code": "shop_context_required", "message": "X-Shop-ID is required."}, status=400)
        try:
            shop_id = UUID(raw_shop_id)
        except ValueError:
            return JsonResponse({"code": "invalid_shop_id", "message": "X-Shop-ID must be a UUID."}, status=400)

        membership = ShopMembership.objects.unscoped().filter(user=request.user, shop_id=shop_id, is_active=True).first()
        if membership is None:
            return JsonResponse({"code": "shop_access_denied", "message": "You do not have access to this shop."}, status=403)

        tokens = set_tenant_context(shop_id)
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('nexora.shop_id', %s, false)", [str(shop_id)])
        request.shop = membership.shop
        request.membership = membership
        try:
            return self.get_response(request)
        finally:
            if connection.vendor == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('nexora.shop_id', '', false)")
            clear_tenant_context(tokens)
