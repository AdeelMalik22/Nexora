from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Product, ProductVariant
from apps.common.models import TenantModel, TimestampedModel
from apps.tenants.models import Branch


class Cart(TenantModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        HELD = "held", "Held"
        FINALIZED = "finalized", "Finalized"
        ABANDONED = "abandoned", "Abandoned"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="carts")
    cashier = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="carts")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)


class CartItem(TimestampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=19, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0"))])
    discount = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])


class Invoice(TenantModel):
    class Status(models.TextChoices):
        FINALIZED = "finalized", "Finalized"
        VOIDED = "voided", "Voided"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="invoices")
    cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name="invoice")
    invoice_number = models.CharField(max_length=100)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.FINALIZED)
    subtotal = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))
    discount_total = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))
    tax_total = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))
    total = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "invoice_number"), name="unique_invoice_number_per_shop")]


class InvoiceItem(TimestampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=80)
    quantity = models.DecimalField(max_digits=19, decimal_places=6)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4)
    discount = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=19, decimal_places=4)


class InvoiceSequence(TenantModel):
    branch = models.OneToOneField(Branch, on_delete=models.PROTECT, related_name="invoice_sequence")
    next_number = models.PositiveBigIntegerField(default=1)
