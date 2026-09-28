from django.contrib import admin

from .models import Branch, Shop, ShopModule


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "currency", "is_active")
    search_fields = ("name", "slug")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "code", "is_active")
    list_filter = ("is_active", "shop")


@admin.register(ShopModule)
class ShopModuleAdmin(admin.ModelAdmin):
    list_display = ("shop", "module_key", "enabled")
    list_filter = ("enabled", "module_key")
