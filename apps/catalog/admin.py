from django.contrib import admin

from .models import Barcode, Category, Price, PriceList, Product, ProductVariant, TaxCategory, Unit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "parent", "is_active")
    list_filter = ("shop", "is_active")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "symbol", "shop", "precision")


@admin.register(TaxCategory)
class TaxCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "shop", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "shop", "category", "unit", "is_active")
    search_fields = ("name", "sku")
    list_filter = ("shop", "is_active")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "product", "shop", "is_active")
    search_fields = ("name", "sku")


@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    list_display = ("code", "shop", "product", "variant", "is_primary")
    search_fields = ("code",)


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "shop", "is_default", "is_active")


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("amount", "price_list", "product", "variant", "valid_from", "valid_until")
