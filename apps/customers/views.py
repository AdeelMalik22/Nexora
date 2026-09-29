from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import Customer, LedgerEntry
from .serializers import CustomerSerializer, LedgerEntrySerializer
from .services import get_or_create_account, record_entry


class CustomerView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_customers"

    def get(self, request):
        queryset = Customer.objects.select_related("ledger_account")
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(phone__icontains=search)
        return Response(CustomerSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save(shop=request.shop)
        get_or_create_account(shop=request.shop, customer=customer)
        return Response(CustomerSerializer(customer).data, status=201)


class CustomerLedgerView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "view_customer_ledger"

    def get(self, request, customer_id):
        customer = Customer.objects.get(id=customer_id)
        account = get_or_create_account(shop=request.shop, customer=customer)
        return Response({"customer": CustomerSerializer(customer).data, "entries": LedgerEntrySerializer(account.entries.order_by("created_at"), many=True).data})


class CustomerPaymentView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_customer_ledger"

    def post(self, request, customer_id):
        customer = Customer.objects.get(id=customer_id)
        try:
            entry = record_entry(shop=request.shop, customer=customer, entry_type=LedgerEntry.EntryType.PAYMENT, amount=request.data["amount"], description=request.data.get("description", "Customer payment"), reference=request.data.get("reference", ""), actor=request.user, request=request)
        except (KeyError, ValueError) as exc:
            return Response({"code": "invalid_customer_payment", "message": str(exc)}, status=400)
        return Response(LedgerEntrySerializer(entry).data, status=201)
