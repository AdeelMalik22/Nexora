from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role, ShopMembership, User
from apps.catalog.models import Product, Unit
from apps.inventory.models import StockBalance
from apps.payments.models import Payment, PaymentMethod
from apps.tenants.models import Branch, Shop


class CheckoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cashier", password="secret")
        self.shop = Shop.objects.create(name="Sales Shop", slug="sales-shop")
        self.branch = Branch.objects.create(shop=self.shop, name="Main", code="MAIN")
        role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=role, is_owner=True)
        unit = Unit.objects.unscoped().create(shop=self.shop, name="Piece", symbol="pc")
        self.product = Product.objects.unscoped().create(shop=self.shop, name="Coffee", sku="COFFEE", unit=unit)
        StockBalance.objects.unscoped().create(shop=self.shop, branch=self.branch, product=self.product, quantity=10)
        self.method = PaymentMethod.objects.unscoped().create(shop=self.shop, name="Cash", code="cash")
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_checkout_deducts_stock_and_records_payment(self):
        response = self.client.post(reverse("sales-carts"), {"branch": str(self.branch.id)}, format="json")
        self.assertEqual(response.status_code, 201)
        cart_id = response.data["id"]
        response = self.client.post(
            reverse("sales-cart-items", args=(cart_id,)),
            {"product": str(self.product.id), "quantity": "2", "unit_price": "100"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            reverse("sales-cart-finalize", args=(cart_id,)),
            {"payments": [{"payment_method": str(self.method.id), "amount": "200"}]},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["total"], "200.0000")
        self.assertEqual(StockBalance.objects.unscoped().get(product=self.product).quantity, Decimal("8"))
        self.assertEqual(Payment.objects.count(), 1)

    def test_payment_mismatch_rolls_back_invoice_and_stock(self):
        response = self.client.post(reverse("sales-carts"), {"branch": str(self.branch.id)}, format="json")
        cart_id = response.data["id"]
        self.client.post(reverse("sales-cart-items", args=(cart_id,)), {"product": str(self.product.id), "quantity": "2", "unit_price": "100"}, format="json")
        response = self.client.post(reverse("sales-cart-finalize", args=(cart_id,)), {"payments": [{"payment_method": str(self.method.id), "amount": "100"}]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockBalance.objects.unscoped().get(product=self.product).quantity, Decimal("10"))

    def test_return_restores_stock_and_creates_credit_note(self):
        response = self.client.post(reverse("sales-carts"), {"branch": str(self.branch.id)}, format="json")
        cart_id = response.data["id"]
        self.client.post(reverse("sales-cart-items", args=(cart_id,)), {"product": str(self.product.id), "quantity": "2", "unit_price": "100"}, format="json")
        response = self.client.post(reverse("sales-cart-finalize", args=(cart_id,)), {"payments": [{"payment_method": str(self.method.id), "amount": "200"}]}, format="json")
        invoice_item = response.data["items"][0]
        response = self.client.post(reverse("sales-returns"), {"invoice": response.data["id"], "branch": str(self.branch.id), "reason": "Damaged", "items": [{"invoice_item": invoice_item["id"], "quantity": "1"}], "refund_amount": "100"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(StockBalance.objects.unscoped().get(product=self.product).quantity, Decimal("9"))

    def test_shift_close_records_cash_variance(self):
        response = self.client.post(reverse("sales-shifts"), {"branch": str(self.branch.id), "opening_cash": "100"}, format="json")
        self.assertEqual(response.status_code, 201)
        response = self.client.post(reverse("sales-shift-close", args=(response.data["id"],)), {"closing_cash": "90"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cash_variance"], "-10.0000")
