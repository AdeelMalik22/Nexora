from rest_framework import serializers

from .models import Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ("id", "device_id", "name", "platform", "last_seen_at", "created_at")
        read_only_fields = ("id", "last_seen_at", "created_at")
