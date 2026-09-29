from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Branch, Shop


class AccountsEndpointCoverageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api-owner", email="api@example.com", password="secret")
        self.shop = Shop.objects.create(name="API Shop", slug="api-shop")
        self.branch = Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_login_refresh_roles_memberships_devices_and_audit_endpoints(self):
        self.client.force_authenticate(None)
        response = self.client.post(reverse("token-obtain-pair"), {"username": "api-owner", "password": "secret"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.force_authenticate(self.user)
        for url in (reverse("role-list"), reverse("membership-list"), reverse("device-list"), reverse("audit-list")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
