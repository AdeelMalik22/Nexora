from rest_framework import serializers

from .models import Customer, LedgerEntry


class CustomerSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(source="ledger_account.balance", max_digits=19, decimal_places=4, read_only=True, default="0")

    class Meta:
        model = Customer
        fields = ("id", "name", "phone", "email", "address", "credit_limit", "balance", "is_active")
        read_only_fields = ("id", "balance")


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ("id", "entry_type", "amount", "description", "invoice", "reference", "created_at")
