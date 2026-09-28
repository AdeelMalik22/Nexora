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
from .serializers import (
    DeviceSerializer,
    InvitationAcceptSerializer,
    InvitationSerializer,
    MembershipSerializer,
    RoleSerializer,
)

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
        raw_credential = secrets.token_urlsafe(32)
        device, created = Device.objects.update_or_create(
            shop=request.shop,
            device_id=serializer.validated_data["device_id"],
            defaults={
                "user": request.user,
                "name": serializer.validated_data["name"],
                "platform": serializer.validated_data.get("platform", ""),
                "last_seen_at": timezone.now(),
                "credential_hash": hashlib.sha256(raw_credential.encode()).hexdigest(),
                "credential_created_at": timezone.now(),
            },
        )
        if created:
            record_event(shop=request.shop, action="device.registered", object_type="Device", object_id=device.id, actor=request.user, request=request)
        response = DeviceSerializer(device).data
        if created:
            response["device_credential"] = raw_credential
        return Response(response, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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


class MembershipActionView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_staff"

    def post(self, request, membership_id, action):
        membership = ShopMembership.objects.get(id=membership_id)
        if membership.is_owner:
            return Response({"code": "owner_membership_protected"}, status=status.HTTP_400_BAD_REQUEST)
        if action == "deactivate":
            membership.is_active = False
            event = "staff.deactivated"
        elif action == "activate":
            membership.is_active = True
            event = "staff.activated"
        else:
            return Response({"code": "invalid_membership_action"}, status=status.HTTP_400_BAD_REQUEST)
        membership.save(update_fields=("is_active", "updated_at"))
        record_event(shop=request.shop, action=event, object_type="ShopMembership", object_id=membership.id, actor=request.user, request=request)
        return Response(MembershipSerializer(membership).data)


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


class InvitationAcceptView(APIView):
    permission_classes = ()

    @transaction.atomic
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_hash = hashlib.sha256(serializer.validated_data["token"].encode()).hexdigest()
        invitation = StaffInvitation.objects.unscoped().select_related("shop", "role").filter(token_hash=token_hash).first()
        if invitation is None or invitation.accepted_at is not None or invitation.expires_at <= timezone.now():
            return Response({"code": "invalid_invitation", "message": "The invitation is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email__iexact=invitation.email).first()
        if user is None:
            username = serializer.validated_data.get("username") or invitation.email.split("@", 1)[0]
            user = User.objects.create_user(username=username, email=invitation.email, password=serializer.validated_data["password"])
        else:
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=("password",))
        membership, _ = ShopMembership.objects.unscoped().get_or_create(
            shop=invitation.shop, user=user, defaults={"role": invitation.role}
        )
        membership.role = invitation.role
        membership.is_active = True
        membership.save(update_fields=("role", "is_active", "updated_at"))
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=("accepted_at", "updated_at"))
        record_event(shop=invitation.shop, action="staff.invitation_accepted", object_type="StaffInvitation", object_id=invitation.id, actor=user, request=request)
        return Response({"user_id": user.id, "shop_id": invitation.shop_id, "membership_id": membership.id}, status=status.HTTP_200_OK)
