from django.urls import path

from .views import CartFinalizeView, CartItemView, CartView, InvoiceView

urlpatterns = [
    path("carts/", CartView.as_view(), name="sales-carts"),
    path("carts/<uuid:cart_id>/items/", CartItemView.as_view(), name="sales-cart-items"),
    path("carts/<uuid:cart_id>/finalize/", CartFinalizeView.as_view(), name="sales-cart-finalize"),
    path("invoices/", InvoiceView.as_view(), name="sales-invoices"),
]
