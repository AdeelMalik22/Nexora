from django.urls import path

from .views import BarcodeView, CategoryView, PriceListView, PriceView, ProductView, TaxCategoryView, UnitView, VariantView

urlpatterns = [
    path("categories/", CategoryView.as_view(), name="catalog-categories"),
    path("units/", UnitView.as_view(), name="catalog-units"),
    path("tax-categories/", TaxCategoryView.as_view(), name="catalog-tax-categories"),
    path("products/", ProductView.as_view(), name="catalog-products"),
    path("variants/", VariantView.as_view(), name="catalog-variants"),
    path("barcodes/", BarcodeView.as_view(), name="catalog-barcodes"),
    path("price-lists/", PriceListView.as_view(), name="catalog-price-lists"),
    path("prices/", PriceView.as_view(), name="catalog-prices"),
]
