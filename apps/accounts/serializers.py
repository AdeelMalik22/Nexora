from rest_framework import serializers

from .models import Device, Role, ShopMembership, StaffInvitation


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "device_id", "name", "platform", "last_seen_at", "approved_at", "revoked_at", "created_at")
        read_only_fields = ("id", "last_seen_at", "approved_at", "revoked_at", "created_at")


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "permissions")


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = ShopMembership
        fields = ("id", "user", "user_email", "role", "role_name", "is_owner", "is_active", "joined_at")
        read_only_fields = ("id", "user", "user_email", "is_owner", "joined_at")


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffInvitation
        fields = ("id", "email", "role", "expires_at", "accepted_at", "created_at")
        read_only_fields = ("id", "accepted_at", "created_at")


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, min_length=8)
