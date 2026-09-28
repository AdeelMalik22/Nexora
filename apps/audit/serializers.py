from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = (
            "id", "actor", "action", "object_type", "object_id", "request_id",
            "device_id", "before", "after", "reason", "created_at",
        )
