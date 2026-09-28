from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "view_audit_log"

    def get(self, request):
        queryset = AuditLog.objects.select_related("actor").order_by("-created_at")
        action = request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)
        return Response(AuditLogSerializer(queryset[:200], many=True).data)
