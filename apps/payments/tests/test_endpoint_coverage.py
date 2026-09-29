from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Shop


class PaymentEndpointCoverageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="payment-api", password="secret")
        self.shop = Shop.objects.create(name="Payment API", slug="payment-api")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_payment_methods_endpoint(self):
        response = self.client.post(reverse("payment-methods"), {"name": "Cash", "code": "cash"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get(reverse("payment-methods")).status_code, 200)
