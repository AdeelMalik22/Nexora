from django.test import TestCase

from apps.common.context import clear_tenant_context, set_tenant_context
from apps.tenants.models import Shop

from apps.accounts.models import Device, Role, ShopMembership, User


class TenantScopeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="secret")
        self.shop_a = Shop.objects.create(name="A", slug="shop-a")
        self.shop_b = Shop.objects.create(name="B", slug="shop-b")
        role_a = Role.objects.create(shop=self.shop_a, name="Owner")
        role_b = Role.objects.create(shop=self.shop_b, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop_a, user=self.user, role=role_a, is_owner=True)
        ShopMembership.objects.unscoped().create(shop=self.shop_b, user=self.user, role=role_b, is_owner=True)
        Device.objects.unscoped().create(shop=self.shop_a, user=self.user, device_id="a", name="A")
        Device.objects.unscoped().create(shop=self.shop_b, user=self.user, device_id="b", name="B")

    def test_tenant_manager_only_returns_current_shop(self):
        tokens = set_tenant_context(self.shop_a.id)
        try:
            self.assertEqual(list(Device.objects.order_by("device_id").values_list("device_id", flat=True)), ["a"])
        finally:
            clear_tenant_context(tokens)

    def test_tenant_manager_fails_closed_without_context(self):
        self.assertEqual(Device.objects.count(), 0)
