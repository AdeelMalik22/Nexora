from django.conf import settings
from django.db import models

from apps.common.models import TenantModel


class AuditLog(TenantModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=120)
    object_id = models.CharField(max_length=64)
    request_id = models.CharField(max_length=64, blank=True)
    device_id = models.CharField(max_length=128, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
