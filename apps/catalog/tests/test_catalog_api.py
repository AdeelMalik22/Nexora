from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Shop

from apps.catalog.models import Barcode, Category, Product, Unit


class CatalogAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="catalog-owner", password="secret")
        self.shop = Shop.objects.create(name="Catalog Shop", slug="catalog-shop")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_product_and_barcode_creation(self):
        unit = Unit.objects.unscoped().create(shop=self.shop, name="Piece", symbol="pc")
        category = Category.objects.unscoped().create(shop=self.shop, name="Grocery")
        response = self.client.post(
            reverse("catalog-products"),
            {"name": "Rice", "sku": "RICE-001", "unit": str(unit.id), "category": str(category.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        product = Product.objects.unscoped().get(sku="RICE-001")
        response = self.client.post(
            reverse("catalog-barcodes"), {"code": "8900001", "product": str(product.id)}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get(reverse("catalog-barcodes"), {"code": "8900001"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_product_list_is_tenant_scoped(self):
        other_shop = Shop.objects.create(name="Other", slug="other-catalog-shop")
        unit = Unit.objects.unscoped().create(shop=other_shop, name="Piece", symbol="pc")
        Product.objects.unscoped().create(shop=other_shop, name="Hidden", sku="HIDDEN", unit=unit)
        response = self.client.get(reverse("catalog-products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cross_shop_catalog_reference_is_rejected_by_database_scope(self):
        other_shop = Shop.objects.create(name="Other 2", slug="other-catalog-shop-2")
        unit = Unit.objects.unscoped().create(shop=other_shop, name="Piece", symbol="pc")
        response = self.client.post(
            reverse("catalog-products"), {"name": "Invalid", "sku": "INVALID", "unit": str(unit.id)}, format="json"
        )
        self.assertEqual(response.status_code, 400)
