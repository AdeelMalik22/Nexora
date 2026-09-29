from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.catalog.models import Product, Unit
from apps.tenants.models import Branch, Shop


class InventoryEndpointCoverageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="inventory-api", password="secret")
        self.shop = Shop.objects.create(name="Inventory API", slug="inventory-api")
        self.branch = Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        unit = Unit.objects.unscoped().create(shop=self.shop, name="Piece", symbol="pc")
        self.product = Product.objects.unscoped().create(shop=self.shop, name="Item", sku="ITEM", unit=unit)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_inventory_collection_endpoints(self):
        response = self.client.post(reverse("inventory-suppliers"), {"name": "Supplier"}, format="json")
        self.assertEqual(response.status_code, 201)
        for name in ("inventory-suppliers", "inventory-stock", "inventory-movements", "inventory-purchases"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
