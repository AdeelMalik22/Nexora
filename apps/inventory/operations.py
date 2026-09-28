from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_event

from .models import PurchaseItem, PurchaseOrder, StockCount, StockCountItem, StockTransfer, StockTransferItem
from .services import record_movement


@transaction.atomic
def receive_purchase(*, shop, branch, supplier, order_number, items, actor, request=None):
    if supplier.shop_id != shop.id or branch.shop_id != shop.id:
        raise ValueError("Supplier and branch must belong to this shop.")
    order = PurchaseOrder.objects.create(shop=shop, branch=branch, supplier=supplier, order_number=order_number)
    for item in items:
        target = item.get("variant") or item.get("product")
        if (item.get("product") is None) == (item.get("variant") is None) or target.shop_id != shop.id:
            raise ValueError("Each purchase item must target exactly one product or variant in this shop.")
        purchase_item = PurchaseItem.objects.create(
            purchase_order=order,
            product=item.get("product"),
            variant=item.get("variant"),
            quantity=Decimal(str(item["quantity"])),
            unit_cost=Decimal(str(item["unit_cost"])),
        )
        record_movement(
            shop=shop, branch=branch, movement_type="purchase", quantity=Decimal(str(item["quantity"])),
            product=item.get("product"), variant=item.get("variant"), unit_cost=Decimal(str(item["unit_cost"])),
            actor=actor, request=request, reference_type="PurchaseOrder", reference_id=order.id,
        )
    order.status = PurchaseOrder.Status.RECEIVED
    order.received_at = timezone.now()
    order.save(update_fields=("status", "received_at", "updated_at"))
    record_event(shop=shop, action="inventory.purchase_received", object_type="PurchaseOrder", object_id=order.id, actor=actor, request=request)
    return order


@transaction.atomic
def complete_transfer(*, shop, source_branch, destination_branch, reference, items, actor, request=None):
    if source_branch.shop_id != shop.id or destination_branch.shop_id != shop.id or source_branch.id == destination_branch.id:
        raise ValueError("Transfer branches must be different branches in this shop.")
    transfer = StockTransfer.objects.create(shop=shop, source_branch=source_branch, destination_branch=destination_branch, reference=reference)
    for item in items:
        if (item.get("product") is None) == (item.get("variant") is None):
            raise ValueError("Each transfer item must target exactly one product or variant.")
        quantity = Decimal(str(item["quantity"]))
        StockTransferItem.objects.create(transfer=transfer, product=item.get("product"), variant=item.get("variant"), quantity=quantity)
        record_movement(shop=shop, branch=source_branch, movement_type="transfer_out", quantity=-quantity, product=item.get("product"), variant=item.get("variant"), actor=actor, request=request, reference_type="StockTransfer", reference_id=transfer.id)
        record_movement(shop=shop, branch=destination_branch, movement_type="transfer_in", quantity=quantity, product=item.get("product"), variant=item.get("variant"), actor=actor, request=request, reference_type="StockTransfer", reference_id=transfer.id)
    transfer.status = StockTransfer.Status.COMPLETED
    transfer.completed_at = timezone.now()
    transfer.save(update_fields=("status", "completed_at", "updated_at"))
    record_event(shop=shop, action="inventory.transfer_completed", object_type="StockTransfer", object_id=transfer.id, actor=actor, request=request)
    return transfer


@transaction.atomic
def reconcile_count(*, shop, branch, reference, items, actor, request=None):
    if branch.shop_id != shop.id:
        raise ValueError("Branch must belong to this shop.")
    count = StockCount.objects.create(shop=shop, branch=branch, reference=reference)
    for item in items:
        product, variant = item.get("product"), item.get("variant")
        if (product is None) == (variant is None):
            raise ValueError("Each count item must target exactly one product or variant.")
        current = (variant or product).stock_balances.filter(shop=shop, branch=branch).first()
        current_quantity = current.quantity if current else 0
        counted_quantity = Decimal(str(item["counted_quantity"]))
        StockCountItem.objects.create(stock_count=count, product=product, variant=variant, counted_quantity=counted_quantity)
        difference = counted_quantity - current_quantity
        if difference:
            record_movement(shop=shop, branch=branch, movement_type="adjustment", quantity=difference, product=product, variant=variant, actor=actor, request=request, reason=f"Stock count {reference}", reference_type="StockCount", reference_id=count.id)
    count.completed_at = timezone.now()
    count.save(update_fields=("completed_at", "updated_at"))
    record_event(shop=shop, action="inventory.count_reconciled", object_type="StockCount", object_id=count.id, actor=actor, request=request)
    return count
