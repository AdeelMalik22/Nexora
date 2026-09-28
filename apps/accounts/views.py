import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.tenants.models import Branch, Shop

from .models import Device, Role, ShopMembership, StaffInvitation
from .permissions import HasShopPermission, TenantContextPermission
from .serializers import DeviceSerializer, InvitationSerializer, MembershipSerializer, RoleSerializer

User = get_user_model()


class SignupView(APIView):
    permission_classes = ()

    @transaction.atomic
    def post(self, request):
        required = ("username", "email", "password", "shop_name", "branch_name")
        missing = [field for field in required if not request.data.get(field)]
        if missing:
            return Response({"code": "required_fields", "fields": missing}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(
            username=request.data["username"],
            email=request.data["email"],
            password=request.data["password"],
        )
        shop = Shop.objects.create(name=request.data["shop_name"], slug=secrets.token_urlsafe(8).lower())
        Branch.objects.create(shop=shop, name=request.data["branch_name"], code="MAIN")
        role = Role.objects.create(shop=shop, name="Owner")
        ShopMembership.objects.create(shop=shop, user=user, role=role, is_owner=True)
        record_event(shop=shop, action="shop.created", object_type="Shop", object_id=shop.id, actor=user, request=request)
        return Response({"user_id": user.id, "shop_id": shop.id, "branch_id": shop.branches.first().id}, status=status.HTTP_201_CREATED)


class DeviceRegistrationView(APIView):
    permission_classes = (TenantContextPermission,)

    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device, created = Device.objects.update_or_create(
            shop=request.shop,
            device_id=serializer.validated_data["device_id"],
            defaults={
                "user": request.user,
                "name": serializer.validated_data["name"],
                "platform": serializer.validated_data.get("platform", ""),
                "last_seen_at": timezone.now(),
            },
        )
        if created:
            record_event(shop=request.shop, action="device.registered", object_type="Device", object_id=device.id, actor=request.user, request=request)
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DeviceListView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_devices"

    def get(self, request):
        return Response(DeviceSerializer(Device.objects.select_related("user").all(), many=True).data)


class DeviceActionView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_devices"

    def post(self, request, device_id, action):
        device = Device.objects.get(id=device_id)
        if action == "approve":
            device.approved_at = timezone.now()
            device.revoked_at = None
            event = "device.approved"
        elif action == "revoke":
            device.revoked_at = timezone.now()
            event = "device.revoked"
        else:
            return Response({"code": "invalid_device_action"}, status=status.HTTP_400_BAD_REQUEST)
        device.save(update_fields=("approved_at", "revoked_at", "updated_at"))
        record_event(shop=request.shop, action=event, object_type="Device", object_id=device.id, actor=request.user, request=request)
        return Response(DeviceSerializer(device).data)


class RoleListView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_roles"

    def get(self, request):
        return Response(RoleSerializer(Role.objects.filter(shop=request.shop), many=True).data)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save(shop=request.shop)
        record_event(shop=request.shop, action="role.created", object_type="Role", object_id=role.id, actor=request.user, request=request)
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class MembershipListView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_staff"

    def get(self, request):
        return Response(MembershipSerializer(ShopMembership.objects.select_related("user", "role").all(), many=True).data)


class InvitationCreateView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_staff"

    @transaction.atomic
    def post(self, request):
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_token = secrets.token_urlsafe(32)
        invitation = serializer.save(
            shop=request.shop,
            invited_by=request.user,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(days=7),
        )
        record_event(shop=request.shop, action="staff.invited", object_type="StaffInvitation", object_id=invitation.id, actor=request.user, request=request)
        return Response({"invitation": InvitationSerializer(invitation).data, "token": raw_token}, status=status.HTTP_201_CREATED)
