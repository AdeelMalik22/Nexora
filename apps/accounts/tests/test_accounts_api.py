from django.urls import reverse
from rest_framework.test import APITestCase

from apps.tenants.models import Shop

from apps.accounts.models import Device, Role, ShopMembership, User


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", email="owner@example.com", password="secret")
        self.shop = Shop.objects.create(name="Test Shop", slug="test-shop")
        self.role = Role.objects.create(shop=self.shop, name="Owner")
        ShopMembership.objects.unscoped().create(shop=self.shop, user=self.user, role=self.role, is_owner=True)
        self.client.force_authenticate(self.user)
        self.client.defaults["HTTP_X_SHOP_ID"] = str(self.shop.id)

    def test_signup_creates_complete_owner_setup(self):
        self.client.force_authenticate(None)
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-owner",
                "email": "new@example.com",
                "password": "strong-password",
                "shop_name": "New Shop",
                "branch_name": "Main",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Shop.objects.filter(id=response.data["shop_id"]).exists())
        new_user = User.objects.get(id=response.data["user_id"])
        self.assertTrue(ShopMembership.objects.unscoped().filter(user=new_user, is_owner=True).exists())

    def test_device_registration_requires_shop_context_and_starts_unapproved(self):
        response = self.client.post(
            reverse("device-register"),
            {"device_id": "counter-01", "name": "Counter", "platform": "android"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("device_credential", response.data)
        self.assertIsNone(Device.objects.unscoped().get(device_id="counter-01").approved_at)

    def test_invitation_can_be_accepted_once(self):
        staff_role = Role.objects.create(shop=self.shop, name="Cashier")
        response = self.client.post(
            reverse("invitation-create"),
            {"email": "cashier@example.com", "role": str(staff_role.id), "expires_at": "2099-01-01T00:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        token = response.data["token"]
        self.client.force_authenticate(None)
        response = self.client.post(
            reverse("invitation-accept"),
            {"token": token, "username": "cashier", "password": "strong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ShopMembership.objects.unscoped().filter(user__username="cashier", role=staff_role).exists())
        response = self.client.post(
            reverse("invitation-accept"),
            {"token": token, "username": "cashier-two", "password": "strong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_owner_can_approve_and_revoke_device(self):
        device = Device.objects.unscoped().create(shop=self.shop, user=self.user, device_id="counter-02", name="Counter")
        response = self.client.post(reverse("device-action", args=(device.id, "approve")), format="json")
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertIsNotNone(device.approved_at)
        response = self.client.post(reverse("device-action", args=(device.id, "revoke")), format="json")
        self.assertEqual(response.status_code, 200)
        device.refresh_from_db()
        self.assertIsNotNone(device.revoked_at)

    def test_membership_cannot_access_another_shop(self):
        other_shop = Shop.objects.create(name="Other Shop", slug="other-shop")
        self.client.defaults["HTTP_X_SHOP_ID"] = str(other_shop.id)
        response = self.client.get(reverse("membership-list"))
        self.assertEqual(response.status_code, 403)
