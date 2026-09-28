from django.db import connection

from .context import clear_tenant_context


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        finally:
            tokens = getattr(request, "_tenant_context_tokens", None)
            if tokens is not None:
                if connection.vendor == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT set_config('nexora.shop_id', '', false)")
                clear_tenant_context(tokens)
