from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel, TimestampedModel
from apps.sales.models import Invoice


class PaymentMethod(TenantModel):
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=40)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "code"), name="unique_payment_method_per_shop")]


class Payment(TimestampedModel):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        REFUNDED = "refunded", "Refunded"

    shop = models.ForeignKey("tenants.Shop", on_delete=models.PROTECT, related_name="payments")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.COMPLETED)
    reference = models.CharField(max_length=120, blank=True)
