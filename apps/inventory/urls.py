from django.urls import path

from .views import MovementView, PurchaseOrderView, StockView, SupplierView

urlpatterns = [
    path("suppliers/", SupplierView.as_view(), name="inventory-suppliers"),
    path("stock/", StockView.as_view(), name="inventory-stock"),
    path("movements/", MovementView.as_view(), name="inventory-movements"),
    path("purchases/", PurchaseOrderView.as_view(), name="inventory-purchases"),
]
