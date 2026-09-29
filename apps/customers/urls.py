from django.urls import path

from .views import CustomerLedgerView, CustomerPaymentView, CustomerView

urlpatterns = [
    path("", CustomerView.as_view(), name="customers"),
    path("<uuid:customer_id>/ledger/", CustomerLedgerView.as_view(), name="customer-ledger"),
    path("<uuid:customer_id>/payments/", CustomerPaymentView.as_view(), name="customer-payment"),
]
