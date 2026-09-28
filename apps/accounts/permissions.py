from rest_framework.permissions import BasePermission


class HasShopPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        membership = getattr(request, "membership", None)
        if membership is None or not membership.is_active:
            return False
        if membership.is_owner or request.user.is_superuser:
            return True
        permission_name = getattr(view, "required_permission", self.required_permission)
        if not permission_name:
            return True
        return membership.role.permissions.filter(codename=permission_name).exists()
