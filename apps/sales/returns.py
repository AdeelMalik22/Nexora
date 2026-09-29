from decimal import Decimal

from django.db import transaction

from apps.audit.services import record_event
from apps.inventory.services import record_movement
from apps.payments.models import Payment, Refund

from .models import CreditNote, Return, ReturnItem


@transaction.atomic
def create_return(*, shop, invoice, branch, items, reason, actor, request=None, refund_amount=Decimal("0")):
    if invoice.shop_id != shop.id or branch.shop_id != shop.id:
        raise ValueError("Invoice and branch must belong to this shop.")
    returned = Return.objects.create(shop=shop, invoice=invoice, branch=branch, reason=reason)
    total = Decimal("0")
    for item in items:
        invoice_item = invoice.items.filter(id=item["invoice_item"]).first()
        quantity = Decimal(str(item["quantity"]))
        if invoice_item is None or quantity <= 0 or quantity > invoice_item.quantity:
            raise ValueError("Return quantity is invalid for the invoice item.")
        amount = (invoice_item.unit_price * quantity).quantize(Decimal("0.0001"))
        ReturnItem.objects.create(return_record=returned, invoice_item=invoice_item, quantity=quantity, amount=amount)
        record_movement(shop=shop, branch=branch, movement_type="return", quantity=quantity, product=invoice_item.product, variant=invoice_item.variant, actor=actor, request=request, reference_type="Return", reference_id=returned.id, reason=reason)
        total += amount
    returned.total = total
    returned.save(update_fields=("total", "updated_at"))
    CreditNote.objects.create(shop=shop, return_record=returned, number=f"CN-{returned.id.hex[:12].upper()}", amount=total)
    if refund_amount:
        remaining = Decimal(str(refund_amount))
        for payment in Payment.objects.filter(invoice=invoice, status=Payment.Status.COMPLETED).order_by("created_at"):
            existing = sum((refund.amount for refund in payment.refunds.all()), Decimal("0"))
            available = payment.amount - existing
            refund = min(available, remaining)
            if refund > 0:
                Refund.objects.create(payment=payment, amount=refund, reason=reason)
                remaining -= refund
            if remaining <= 0:
                break
        if remaining > 0:
            raise ValueError("Refund exceeds available payment amount.")
    record_event(shop=shop, action="sales.return_created", object_type="Return", object_id=returned.id, actor=actor, request=request, after={"total": str(total)})
    return returned
