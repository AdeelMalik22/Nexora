from django.contrib import admin

from .models import PurchaseItem, PurchaseOrder, StockBalance, StockMovement, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "phone", "is_active")
    search_fields = ("name", "phone", "email")


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("branch", "product", "variant", "quantity", "low_stock_threshold")
    list_filter = ("shop", "branch")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("branch", "product", "variant", "movement_type", "quantity", "created_at")
    list_filter = ("shop", "branch", "movement_type")
    readonly_fields = ("created_at", "updated_at")


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "supplier", "branch", "status", "received_at")
    list_filter = ("shop", "status")
    inlines = (PurchaseItemInline,)
