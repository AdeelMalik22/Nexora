from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Shop


class CatalogEndpointCoverageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="catalog-api", password="secret")
        self.shop = Shop.objects.create(name="Catalog API", slug="catalog-api")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_catalog_collection_endpoints(self):
        cases = (
            ("catalog-categories", {"name": "Food"}),
            ("catalog-units", {"name": "Piece", "symbol": "pc"}),
            ("catalog-tax-categories", {"name": "Standard", "rate": "17"}),
            ("catalog-price-lists", {"name": "Retail", "currency": "PKR"}),
        )
        for name, payload in cases:
            response = self.client.post(reverse(name), payload, format="json")
            self.assertEqual(response.status_code, 201, name)
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
