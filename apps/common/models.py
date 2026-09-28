import uuid

from django.db import models

from .context import current_shop_id


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(UUIDModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class TenantQuerySet(models.QuerySet):
    def for_current_shop(self):
        shop_id = current_shop_id()
        if shop_id is None:
            return self.none()
        return self.filter(shop_id=shop_id)

    def unscoped(self):
        return self.all()


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    def get_queryset(self):
        return super().get_queryset().for_current_shop()

    def unscoped(self):
        return super().get_queryset()


class TenantModel(TimestampedModel):
    shop = models.ForeignKey("tenants.Shop", on_delete=models.PROTECT)
    objects = TenantManager()

    class Meta:
        abstract = True
