from rest_framework import serializers

from .models import PurchaseItem, PurchaseOrder, StockBalance, StockMovement, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("id", "name", "phone", "email", "address", "is_active")
        read_only_fields = ("id",)


class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBalance
        fields = ("id", "branch", "product", "variant", "quantity", "low_stock_threshold")
        read_only_fields = ("id", "quantity")


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ("id", "branch", "product", "variant", "movement_type", "quantity", "unit_cost", "reason", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        if bool(attrs.get("product")) == bool(attrs.get("variant")):
            raise serializers.ValidationError({"target": "Provide exactly one product or variant."})
        shop = self.context["request"].shop
        target = attrs.get("variant") or attrs.get("product")
        branch = attrs.get("branch")
        if target.shop_id != shop.id or branch.shop_id != shop.id:
            raise serializers.ValidationError({"target": "The stock target and branch must belong to this shop."})
        return attrs


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = ("id", "product", "variant", "quantity", "unit_cost")
        read_only_fields = ("id",)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ("id", "branch", "supplier", "status", "order_number", "received_at", "items")
        read_only_fields = ("id", "status", "received_at", "items")
