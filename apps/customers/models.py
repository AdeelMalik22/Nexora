from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel, TimestampedModel


class Customer(TenantModel):
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("shop", "phone"), condition=~models.Q(phone=""), name="unique_customer_phone_per_shop")]
        ordering = ("name",)


class LedgerAccount(TenantModel):
    customer = models.OneToOneField(Customer, on_delete=models.PROTECT, related_name="ledger_account")
    balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal("0"))


class LedgerEntry(TimestampedModel):
    class EntryType(models.TextChoices):
        CHARGE = "charge", "Charge"
        PAYMENT = "payment", "Payment"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="entries")
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    description = models.CharField(max_length=240)
    invoice = models.ForeignKey("sales.Invoice", null=True, blank=True, on_delete=models.PROTECT, related_name="ledger_entries")
    reference = models.CharField(max_length=120, blank=True)
