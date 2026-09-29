from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_event

from .models import CashDrawerEntry, Shift


@transaction.atomic
def open_shift(*, shop, branch, cashier, opening_cash, actor, request=None):
    if Shift.objects.filter(shop=shop, branch=branch, cashier=cashier, status=Shift.Status.OPEN).exists():
        raise ValueError("Cashier already has an open shift.")
    shift = Shift.objects.create(shop=shop, branch=branch, cashier=cashier, opening_cash=Decimal(str(opening_cash)))
    record_event(shop=shop, action="shift.opened", object_type="Shift", object_id=shift.id, actor=actor, request=request)
    return shift


@transaction.atomic
def close_shift(*, shop, shift, closing_cash, actor, request=None):
    if shift.shop_id != shop.id or shift.status != Shift.Status.OPEN:
        raise ValueError("Shift is not open for this shop.")
    expected = shift.opening_cash + sum((entry.amount for entry in shift.cash_entries.all()), Decimal("0"))
    closing_cash = Decimal(str(closing_cash))
    shift.closing_cash = closing_cash
    shift.cash_variance = closing_cash - expected
    shift.status = Shift.Status.CLOSED
    shift.closed_at = timezone.now()
    shift.save(update_fields=("closing_cash", "cash_variance", "status", "closed_at", "updated_at"))
    record_event(shop=shop, action="shift.closed", object_type="Shift", object_id=shift.id, actor=actor, request=request, after={"variance": str(shift.cash_variance)})
    return shift
