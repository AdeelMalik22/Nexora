from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from django.db.models import Sum
from django.utils import timezone

from apps.customers.models import LedgerAccount
from apps.inventory.models import StockBalance
from apps.payments.models import Payment
from apps.sales.models import Invoice, Shift


def date_window(request):
    today = timezone.localdate()
    start = datetime.fromisoformat(request.query_params.get("from", str(today))) if request.query_params.get("from") else datetime.combine(today, time.min)
    end = datetime.fromisoformat(request.query_params.get("to", str(today))) if request.query_params.get("to") else datetime.combine(today, time.max)
    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    if timezone.is_naive(end):
        end = timezone.make_aware(end)
    return start, end


def scoped_invoices(shop, request):
    start, end = date_window(request)
    queryset = Invoice.objects.filter(shop=shop, created_at__range=(start, end), status=Invoice.Status.FINALIZED)
    branch = request.query_params.get("branch")
    if branch:
        try:
            UUID(branch)
        except ValueError:
            return queryset.none()
        return queryset.filter(branch_id=branch)
    return queryset


def daily_report(shop, request):
    invoices = scoped_invoices(shop, request)
    totals = invoices.aggregate(subtotal=Sum("subtotal"), discount=Sum("discount_total"), tax=Sum("tax_total"), total=Sum("total"))
    payments = Payment.objects.filter(shop=shop, invoice__in=invoices).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return {"invoice_count": invoices.count(), "subtotal": totals["subtotal"] or Decimal("0"), "discount": totals["discount"] or Decimal("0"), "tax": totals["tax"] or Decimal("0"), "sales_total": totals["total"] or Decimal("0"), "payments_total": payments}


def profit_report(shop, request):
    invoices = scoped_invoices(shop, request)
    sales = invoices.aggregate(total=Sum("total"))["total"] or Decimal("0")
    # Cost data is added when purchase cost layers are introduced; this remains explicit.
    return {"sales_total": sales, "estimated_cost": Decimal("0"), "estimated_profit": sales, "cost_status": "not_available"}


def stock_report(shop, request):
    queryset = StockBalance.objects.filter(shop=shop).select_related("product", "variant", "branch")
    branch = request.query_params.get("branch")
    if branch:
        queryset = queryset.filter(branch_id=branch)
    rows = []
    for balance in queryset:
        rows.append({"branch": str(balance.branch_id), "product": str(balance.product_id) if balance.product_id else None, "variant": str(balance.variant_id) if balance.variant_id else None, "quantity": balance.quantity, "low_stock": balance.quantity <= balance.low_stock_threshold})
    return {"items": rows, "low_stock_count": sum(1 for row in rows if row["low_stock"])}


def credit_report(shop):
    accounts = LedgerAccount.objects.filter(shop=shop).select_related("customer")
    return [{"customer": str(account.customer_id), "name": account.customer.name, "balance": account.balance, "credit_limit": account.customer.credit_limit} for account in accounts]


def cash_report(shop, request):
    start, end = date_window(request)
    shifts = Shift.objects.filter(shop=shop, opened_at__range=(start, end))
    return {"shift_count": shifts.count(), "closing_cash": shifts.aggregate(total=Sum("closing_cash"))["total"] or Decimal("0"), "variance": shifts.aggregate(total=Sum("cash_variance"))["total"] or Decimal("0")}
