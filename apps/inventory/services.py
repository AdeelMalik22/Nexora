from django.db import transaction

from apps.audit.services import record_event

from .models import StockBalance, StockMovement


@transaction.atomic
def record_movement(*, shop, branch, movement_type, quantity, product=None, variant=None, unit_cost=None, actor=None, request=None, reason="", reference_type="", reference_id=None):
    if (product is None) == (variant is None):
        raise ValueError("Provide exactly one product or variant.")
    target = variant or product
    if target.shop_id != shop.id or branch.shop_id != shop.id:
        raise ValueError("The stock target and branch must belong to the current shop.")
    filters = {"shop": shop, "branch": branch, "product": product, "variant": variant}
    balance, _ = StockBalance.objects.select_for_update().get_or_create(**filters)
    movement = StockMovement.objects.create(
        shop=shop,
        branch=branch,
        product=product,
        variant=variant,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=unit_cost,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    balance.quantity += quantity
    balance.save(update_fields=("quantity", "updated_at"))
    record_event(
        shop=shop,
        action="inventory.movement_recorded",
        object_type="StockMovement",
        object_id=movement.id,
        actor=actor,
        request=request,
        after={"quantity": str(quantity), "movement_type": movement_type, "balance": str(balance.quantity)},
        reason=reason,
    )
    return movement, balance
