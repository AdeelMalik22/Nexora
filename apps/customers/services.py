from decimal import Decimal

from django.db import transaction

from apps.audit.services import record_event

from .models import Customer, LedgerAccount, LedgerEntry


@transaction.atomic
def get_or_create_account(*, shop, customer):
    if customer.shop_id != shop.id:
        raise ValueError("Customer belongs to another shop.")
    account, _ = LedgerAccount.objects.select_for_update().get_or_create(shop=shop, customer=customer)
    return account


@transaction.atomic
def record_entry(*, shop, customer, entry_type, amount, description, actor=None, request=None, invoice=None, reference=""):
    account = get_or_create_account(shop=shop, customer=customer)
    amount = Decimal(str(amount))
    if entry_type in (LedgerEntry.EntryType.PAYMENT, LedgerEntry.EntryType.REFUND):
        signed = -amount
    else:
        signed = amount
    new_balance = account.balance + signed
    if new_balance > customer.credit_limit and entry_type == LedgerEntry.EntryType.CHARGE:
        raise ValueError("Customer credit limit exceeded.")
    entry = LedgerEntry.objects.create(account=account, entry_type=entry_type, amount=signed, description=description, invoice=invoice, reference=reference)
    account.balance = new_balance
    account.save(update_fields=("balance", "updated_at"))
    record_event(shop=shop, action=f"customers.ledger_{entry_type}", object_type="LedgerEntry", object_id=entry.id, actor=actor, request=request, after={"balance": str(new_balance)})
    return entry
