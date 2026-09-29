from django.urls import path

from .returns_views import ReturnView, ShiftCloseView, ShiftView
from .views import CartFinalizeView, CartItemView, CartView, InvoiceView

urlpatterns = [
    path("carts/", CartView.as_view(), name="sales-carts"),
    path("carts/<uuid:cart_id>/items/", CartItemView.as_view(), name="sales-cart-items"),
    path("carts/<uuid:cart_id>/finalize/", CartFinalizeView.as_view(), name="sales-cart-finalize"),
    path("invoices/", InvoiceView.as_view(), name="sales-invoices"),
    path("returns/", ReturnView.as_view(), name="sales-returns"),
    path("shifts/", ShiftView.as_view(), name="sales-shifts"),
    path("shifts/<uuid:shift_id>/close/", ShiftCloseView.as_view(), name="sales-shift-close"),
]
