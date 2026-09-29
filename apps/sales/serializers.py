from rest_framework import serializers

from .models import Cart, CartItem, Invoice, InvoiceItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ("id", "product", "variant", "quantity", "unit_price", "discount")
        read_only_fields = ("id",)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "branch", "cashier", "status", "items", "created_at")
        read_only_fields = ("id", "cashier", "status", "items", "created_at")


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ("product_name", "sku", "quantity", "unit_price", "discount", "tax_rate", "line_total")


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = ("id", "invoice_number", "branch", "status", "subtotal", "discount_total", "tax_total", "total", "items", "created_at")
