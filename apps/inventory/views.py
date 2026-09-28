from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission
from apps.catalog.models import Product, ProductVariant

from .models import PurchaseOrder, StockBalance, StockMovement, Supplier
from .operations import complete_transfer, receive_purchase, reconcile_count
from .serializers import PurchaseOrderSerializer, StockBalanceSerializer, StockMovementSerializer, SupplierSerializer
from .services import record_movement


def resolve_items(shop, raw_items):
    resolved = []
    for raw in raw_items:
        item = dict(raw)
        if item.get("product"):
            item["product"] = Product.objects.unscoped().filter(id=item["product"], shop=shop).first()
        if item.get("variant"):
            item["variant"] = ProductVariant.objects.unscoped().filter(id=item["variant"], shop=shop).first()
        resolved.append(item)
    return resolved


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


class PurchaseReceiveView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_inventory"

    @transaction.atomic
    def post(self, request):
        supplier = Supplier.objects.filter(id=request.data.get("supplier"), shop=request.shop).first()
        branch = request.shop.branches.filter(id=request.data.get("branch"), is_active=True).first()
        if not supplier or not branch or not request.data.get("items"):
            return Response({"code": "invalid_purchase", "message": "Supplier, branch, and items are required."}, status=400)
        try:
            order = receive_purchase(shop=request.shop, branch=branch, supplier=supplier, order_number=request.data["order_number"], items=resolve_items(request.shop, request.data["items"]), actor=request.user, request=request)
        except (KeyError, TypeError, ValueError) as exc:
            return Response({"code": "invalid_purchase", "message": str(exc)}, status=400)
        return Response(PurchaseOrderSerializer(order).data, status=201)


class TransferView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_inventory"

    def post(self, request):
        source = request.shop.branches.filter(id=request.data.get("source_branch"), is_active=True).first()
        destination = request.shop.branches.filter(id=request.data.get("destination_branch"), is_active=True).first()
        try:
            transfer = complete_transfer(shop=request.shop, source_branch=source, destination_branch=destination, reference=request.data["reference"], items=resolve_items(request.shop, request.data["items"]), actor=request.user, request=request)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return Response({"code": "invalid_transfer", "message": str(exc)}, status=400)
        return Response({"id": transfer.id, "status": transfer.status}, status=201)


class StockCountView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "adjust_inventory"

    def post(self, request):
        branch = request.shop.branches.filter(id=request.data.get("branch"), is_active=True).first()
        try:
            count = reconcile_count(shop=request.shop, branch=branch, reference=request.data["reference"], items=resolve_items(request.shop, request.data["items"]), actor=request.user, request=request)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            return Response({"code": "invalid_stock_count", "message": str(exc)}, status=400)
        return Response({"id": count.id, "completed_at": count.completed_at}, status=201)


class StockThresholdView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_inventory"

    def patch(self, request, balance_id):
        balance = StockBalance.objects.get(id=balance_id)
        threshold = request.data.get("low_stock_threshold")
        if threshold is None:
            return Response({"code": "threshold_required"}, status=400)
        balance.low_stock_threshold = threshold
        balance.save(update_fields=("low_stock_threshold", "updated_at"))
        return Response(StockBalanceSerializer(balance).data)
