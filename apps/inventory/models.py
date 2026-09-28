from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.catalog.models import Product, ProductVariant
from apps.common.models import TenantModel, TimestampedModel
from apps.tenants.models import Branch


class Supplier(TenantModel):
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "name"), name="unique_supplier_per_shop")]


class StockBalance(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="stock_balances")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_balances")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_balances")
    quantity = models.DecimalField(max_digits=19, decimal_places=6, default=Decimal("0"))
    low_stock_threshold = models.DecimalField(max_digits=19, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shop", "branch", "product"), condition=models.Q(variant__isnull=True), name="unique_product_balance_per_branch"),
            models.UniqueConstraint(fields=("shop", "branch", "variant"), condition=models.Q(variant__isnull=False), name="unique_variant_balance_per_branch"),
            models.CheckConstraint(condition=models.Q(product__isnull=False) | models.Q(variant__isnull=False), name="balance_has_target"),
        ]


class StockMovement(TenantModel):
    class MovementType(models.TextChoices):
        OPENING = "opening", "Opening balance"
        PURCHASE = "purchase", "Purchase"
        SALE = "sale", "Sale"
        RETURN = "return", "Return"
        ADJUSTMENT = "adjustment", "Adjustment"
        TRANSFER_IN = "transfer_in", "Transfer in"
        TRANSFER_OUT = "transfer_out", "Transfer out"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="stock_movements")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_movements")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=24, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=19, decimal_places=6)
    unit_cost = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, validators=[MinValueValidator(Decimal("0"))])
    reference_type = models.CharField(max_length=80, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=~models.Q(quantity=0), name="movement_quantity_nonzero"),
            models.CheckConstraint(condition=models.Q(product__isnull=False) | models.Q(variant__isnull=False), name="movement_has_target"),
        ]


class PurchaseOrder(TenantModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    order_number = models.CharField(max_length=80)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "order_number"), name="unique_purchase_number_per_shop")]


class PurchaseItem(TimestampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=19, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])
    unit_cost = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(product__isnull=False) | models.Q(variant__isnull=False), name="purchase_item_has_target")]


class StockTransfer(TenantModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    source_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="outgoing_transfers")
    destination_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="incoming_transfers")
    reference = models.CharField(max_length=80)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "reference"), name="unique_transfer_reference_per_shop")]


class StockTransferItem(TimestampedModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=19, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])


class StockCount(TenantModel):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="stock_counts")
    reference = models.CharField(max_length=80)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "reference"), name="unique_stock_count_reference_per_shop")]


class StockCountItem(TimestampedModel):
    stock_count = models.ForeignKey(StockCount, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    counted_quantity = models.DecimalField(max_digits=19, decimal_places=6, validators=[MinValueValidator(Decimal("0"))])
