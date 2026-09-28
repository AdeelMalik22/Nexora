from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device
from .serializers import DeviceSerializer


class DeviceRegistrationView(APIView):
    permission_classes = (IsAuthenticated,)

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
                "revoked_at": None,
            },
        )
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
