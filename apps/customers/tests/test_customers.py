from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.tenants.models import Shop

from apps.customers.models import Customer, LedgerEntry
from apps.customers.services import record_entry


class CustomerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="customer-owner", password="secret")
        self.shop = Shop.objects.create(name="Customer Shop", slug="customer-shop")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_customer_and_payment_ledger(self):
        response = self.client.post(reverse("customers"), {"name": "Ali", "phone": "03001234567", "credit_limit": "1000"}, format="json")
        self.assertEqual(response.status_code, 201)
        customer_id = response.data["id"]
        response = self.client.post(reverse("customer-payment", args=(customer_id,)), {"amount": "100", "description": "Cash received"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LedgerEntry.objects.count(), 1)
        response = self.client.get(reverse("customer-ledger", args=(customer_id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["customer"]["balance"], "-100.0000")

    def test_credit_limit_rejects_excess_charge(self):
        customer = Customer.objects.create(shop=self.shop, name="Limited", credit_limit=Decimal("50"))
        with self.assertRaises(ValueError):
            record_entry(shop=self.shop, customer=customer, entry_type="charge", amount="60", description="Too much credit")
