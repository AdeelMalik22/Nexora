from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.catalog.models import Product, Unit
from apps.tenants.models import Branch, Shop

from apps.inventory.models import StockBalance, StockMovement


class InventoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="inventory-owner", password="secret")
        self.shop = Shop.objects.create(name="Inventory Shop", slug="inventory-shop")
        self.branch = Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.unit = Unit.objects.unscoped().create(shop=self.shop, name="Piece", symbol="pc")
        self.product = Product.objects.unscoped().create(shop=self.shop, name="Rice", sku="RICE", unit=self.unit)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_movement_updates_balance_and_keeps_journal(self):
        response = self.client.post(
            reverse("inventory-movements"),
            {
                "branch": str(self.branch.id),
                "product": str(self.product.id),
                "movement_type": "purchase",
                "quantity": "10",
                "unit_cost": "100.00",
                "reason": "opening stock",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(StockMovement.objects.unscoped().count(), 1)
        self.assertEqual(StockBalance.objects.unscoped().get(product=self.product).quantity, Decimal("10"))

    def test_negative_movement_reduces_balance(self):
        StockBalance.objects.unscoped().create(shop=self.shop, branch=self.branch, product=self.product, quantity=10)
        response = self.client.post(
            reverse("inventory-movements"),
            {"branch": str(self.branch.id), "product": str(self.product.id), "movement_type": "sale", "quantity": "-3"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(StockBalance.objects.unscoped().get(product=self.product).quantity, Decimal("7"))

    def test_cross_shop_branch_is_rejected(self):
        other = Shop.objects.create(name="Other Inventory", slug="other-inventory")
        other_branch = Branch.objects.create(shop=other, name="Other", code="MAIN")
        response = self.client.post(
            reverse("inventory-movements"),
            {"branch": str(other_branch.id), "product": str(self.product.id), "movement_type": "purchase", "quantity": "1"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
