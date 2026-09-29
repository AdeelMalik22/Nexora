from rest_framework import serializers

from .models import Payment, PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ("id", "name", "code", "is_active")
        read_only_fields = ("id",)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "invoice", "payment_method", "amount", "status", "reference", "created_at")
