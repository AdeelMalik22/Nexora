import uuid

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models

from apps.common.models import TenantModel
from apps.tenants.models import Shop


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)


class Role(TenantModel):
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="roles")
    name = models.CharField(max_length=80)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="nexora_roles")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "name"), name="unique_role_per_shop")]


class ShopMembership(TenantModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="memberships")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="memberships")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "user"), name="unique_membership_per_shop")]


class Device(TenantModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="devices")
    device_id = models.CharField(max_length=128)
    name = models.CharField(max_length=120)
    platform = models.CharField(max_length=32, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "device_id"), name="unique_device_per_shop")]

    @property
    def is_revoked(self):
        return self.revoked_at is not None
