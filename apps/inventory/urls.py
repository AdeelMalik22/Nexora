from django.urls import path

from .views import MovementView, PurchaseOrderView, PurchaseReceiveView, StockCountView, StockThresholdView, StockView, SupplierView, TransferView

urlpatterns = [
    path("suppliers/", SupplierView.as_view(), name="inventory-suppliers"),
    path("stock/", StockView.as_view(), name="inventory-stock"),
    path("movements/", MovementView.as_view(), name="inventory-movements"),
    path("purchases/", PurchaseOrderView.as_view(), name="inventory-purchases"),
    path("purchases/receive/", PurchaseReceiveView.as_view(), name="inventory-purchase-receive"),
    path("transfers/", TransferView.as_view(), name="inventory-transfers"),
    path("counts/", StockCountView.as_view(), name="inventory-counts"),
    path("stock/<uuid:balance_id>/threshold/", StockThresholdView.as_view(), name="inventory-threshold"),
]
