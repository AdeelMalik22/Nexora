from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import PaymentMethod
from .serializers import PaymentMethodSerializer


class PaymentMethodView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_payments"

    def get(self, request):
        return Response(PaymentMethodSerializer(PaymentMethod.objects.all(), many=True).data)

    def post(self, request):
        serializer = PaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(PaymentMethodSerializer(serializer.save(shop=request.shop)).data, status=201)
