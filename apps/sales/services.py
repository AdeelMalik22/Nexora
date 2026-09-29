from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.audit.services import record_event
from apps.inventory.services import record_movement
from apps.payments.models import Payment

from .models import Cart, Invoice, InvoiceItem, InvoiceSequence


MONEY = Decimal("0.0001")


@transaction.atomic
def finalize_cart(*, shop, cart_id, payments, actor, request=None):
    cart = Cart.objects.select_for_update().prefetch_related("items__product__tax_category", "items__variant__product__tax_category").get(id=cart_id, shop=shop)
    if cart.status == Cart.Status.FINALIZED:
        return cart.invoice
    if cart.status not in (Cart.Status.OPEN, Cart.Status.HELD):
        raise ValueError("Only open or held carts can be finalized.")
    items = list(cart.items.all())
    if not items:
        raise ValueError("Cannot finalize an empty cart.")
    sequence, _ = InvoiceSequence.objects.select_for_update().get_or_create(shop=shop, branch=cart.branch)
    invoice_number = f"{cart.branch.code}-{sequence.next_number:08d}"
    sequence.next_number += 1
    sequence.save(update_fields=("next_number", "updated_at"))
    invoice = Invoice.objects.create(shop=shop, branch=cart.branch, cart=cart, invoice_number=invoice_number)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    for item in items:
        product = item.variant.product if item.variant else item.product
        tax_rate = product.tax_category.rate if product.tax_category else Decimal("0")
        net = (item.quantity * item.unit_price - item.discount).quantize(MONEY, rounding=ROUND_HALF_UP)
        tax = (net * tax_rate / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)
        InvoiceItem.objects.create(invoice=invoice, product=item.product, variant=item.variant, product_name=product.name, sku=item.variant.sku if item.variant else product.sku, quantity=item.quantity, unit_price=item.unit_price, discount=item.discount, tax_rate=tax_rate, line_total=net + tax)
        record_movement(shop=shop, branch=cart.branch, movement_type="sale", quantity=-item.quantity, product=item.product, variant=item.variant, actor=actor, request=request, reference_type="Invoice", reference_id=invoice.id)
        subtotal += item.quantity * item.unit_price
        discount_total += item.discount
        tax_total += tax
    invoice.subtotal = subtotal.quantize(MONEY)
    invoice.discount_total = discount_total.quantize(MONEY)
    invoice.tax_total = tax_total.quantize(MONEY)
    invoice.total = (invoice.subtotal - invoice.discount_total + invoice.tax_total).quantize(MONEY)
    paid = sum((Decimal(str(payment["amount"])) for payment in payments), Decimal("0"))
    if paid != invoice.total:
        raise ValueError("Payment total must equal invoice total.")
    invoice.save(update_fields=("subtotal", "discount_total", "tax_total", "total", "updated_at"))
    for payment in payments:
        Payment.objects.create(shop=shop, invoice=invoice, payment_method_id=payment["payment_method"], amount=payment["amount"], reference=payment.get("reference", ""))
    cart.status = Cart.Status.FINALIZED
    cart.save(update_fields=("status", "updated_at"))
    record_event(shop=shop, action="sales.invoice_finalized", object_type="Invoice", object_id=invoice.id, actor=actor, request=request, after={"invoice_number": invoice_number, "total": str(invoice.total)})
    return invoice
