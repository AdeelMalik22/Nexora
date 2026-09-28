from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import PurchaseOrder, StockBalance, StockMovement, Supplier
from .serializers import PurchaseOrderSerializer, StockBalanceSerializer, StockMovementSerializer, SupplierSerializer
from .services import record_movement


class SupplierView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_inventory"

    def get(self, request):
        return Response(SupplierSerializer(Supplier.objects.all(), many=True).data)

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save(shop=request.shop)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class StockView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "view_inventory"

    def get(self, request):
        queryset = StockBalance.objects.select_related("branch", "product", "variant")
        if request.query_params.get("branch"):
            queryset = queryset.filter(branch_id=request.query_params["branch"])
        if request.query_params.get("low_stock") == "true":
            queryset = queryset.filter(quantity__lte=models.F("low_stock_threshold"))
        return Response(StockBalanceSerializer(queryset, many=True).data)


class MovementView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "adjust_inventory"

    def get(self, request):
        return Response(StockMovementSerializer(StockMovement.objects.order_by("-created_at")[:200], many=True).data)

    def post(self, request):
        serializer = StockMovementSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            movement, balance = record_movement(shop=request.shop, actor=request.user, request=request, **data)
        except ValueError as exc:
            return Response({"code": "invalid_movement", "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"movement": StockMovementSerializer(movement).data, "balance": StockBalanceSerializer(balance).data}, status=status.HTTP_201_CREATED)


class PurchaseOrderView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_inventory"

    def get(self, request):
        return Response(PurchaseOrderSerializer(PurchaseOrder.objects.prefetch_related("items").all(), many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = PurchaseOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["supplier"].shop_id != request.shop.id or serializer.validated_data["branch"].shop_id != request.shop.id:
            return Response({"code": "cross_shop_reference"}, status=status.HTTP_400_BAD_REQUEST)
        order = serializer.save(shop=request.shop)
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_201_CREATED)
