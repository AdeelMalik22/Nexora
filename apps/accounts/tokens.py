from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Device, ShopMembership


class NexoraTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        shop_id = self.initial_data.get("shop_id")
        device_id = self.initial_data.get("device_id")
        if shop_id:
            membership = ShopMembership.objects.unscoped().filter(user=self.user, shop_id=shop_id, is_active=True).first()
            if membership is None:
                raise self.fail("no_active_account")
            self.user.membership = membership
        else:
            membership = ShopMembership.objects.unscoped().filter(user=self.user, is_active=True).first()
        if membership:
            data["shop_id"] = str(membership.shop_id)
            data["role"] = membership.role.name
        if device_id and membership:
            device = Device.objects.unscoped().filter(shop_id=membership.shop_id, device_id=device_id, user=self.user).first()
            if device is None or not device.is_approved:
                raise self.fail("no_active_account")
            data["device_id"] = device.device_id
        return data
