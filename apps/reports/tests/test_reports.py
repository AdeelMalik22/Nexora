from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Branch, Shop


class ReportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="report-owner", password="secret")
        self.shop = Shop.objects.create(name="Report Shop", slug="report-shop")
        Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_report_endpoints_return_empty_baselines(self):
        for name in ("report-daily", "report-profit", "report-stock", "report-credit", "report-cash"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_reports_accept_date_and_branch_filters(self):
        response = self.client.get(reverse("report-daily"), {"from": "2026-01-01", "to": "2026-01-31", "branch": "missing"})
        self.assertEqual(response.status_code, 200)
