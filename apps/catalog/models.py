from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel
from apps.tenants.models import Shop


class Category(TenantModel):
    name = models.CharField(max_length=120)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "name"), name="unique_category_name_per_shop")]
        ordering = ("name",)


class Unit(TenantModel):
    name = models.CharField(max_length=80)
    symbol = models.CharField(max_length=16)
    precision = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "symbol"), name="unique_unit_symbol_per_shop")]


class TaxCategory(TenantModel):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=7, decimal_places=4, validators=[MinValueValidator(Decimal("0"))])
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "name"), name="unique_tax_category_per_shop")]


class Product(TenantModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="products")
    tax_category = models.ForeignKey(TaxCategory, null=True, blank=True, on_delete=models.PROTECT, related_name="products")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "sku"), name="unique_product_sku_per_shop")]
        ordering = ("name", "sku")


class ProductVariant(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=80)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "sku"), name="unique_variant_sku_per_shop")]


class Barcode(TenantModel):
    code = models.CharField(max_length=64)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT, related_name="barcodes")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="barcodes")
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shop", "code"), name="unique_barcode_per_shop"),
            models.CheckConstraint(condition=models.Q(product__isnull=False) | models.Q(variant__isnull=False), name="barcode_has_target"),
        ]


class PriceList(TenantModel):
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default="PKR")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "name"), name="unique_price_list_per_shop")]


class Price(TenantModel):
    price_list = models.ForeignKey(PriceList, on_delete=models.PROTECT, related_name="prices")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT, related_name="prices")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="prices")
    amount = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0"))])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(product__isnull=False) | models.Q(variant__isnull=False), name="price_has_target")]
