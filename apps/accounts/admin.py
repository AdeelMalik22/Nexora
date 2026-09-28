from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Device, Role, ShopMembership, StaffInvitation, User


@admin.register(User)
class NexoraUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Nexora", {"fields": ("phone",)}),)
    list_display = ("username", "email", "is_active", "is_staff")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "shop")
    list_filter = ("shop",)


@admin.register(ShopMembership)
class ShopMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "shop", "role", "is_active")
    list_filter = ("is_active", "shop", "role")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "user", "shop", "approved_at", "revoked_at")
    list_filter = ("shop", "revoked_at")


@admin.register(StaffInvitation)
class StaffInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "shop", "role", "expires_at", "accepted_at")
    list_filter = ("shop", "role")
