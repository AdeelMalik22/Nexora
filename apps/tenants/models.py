from django.db import models

from apps.common.models import TimestampedModel


class Shop(TimestampedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=3, default="PKR")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Branch(TimestampedModel):
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=32)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shop", "code"), name="unique_branch_code_per_shop"),
        ]
        ordering = ("shop", "name")

    def __str__(self):
        return f"{self.shop.name} / {self.name}"


class ShopModule(TimestampedModel):
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name="modules")
    module_key = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shop", "module_key"), name="unique_module_per_shop"),
        ]
