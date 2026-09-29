from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Branch, Shop


class SalesEndpointCoverageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="sales-api", password="secret")
        self.shop = Shop.objects.create(name="Sales API", slug="sales-api")
        self.branch = Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_sales_collection_endpoints(self):
        response = self.client.post(reverse("sales-shifts"), {"branch": str(self.branch.id), "opening_cash": "0"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get(reverse("sales-carts")).status_code, 200)
        self.assertEqual(self.client.get(reverse("sales-invoices")).status_code, 200)
