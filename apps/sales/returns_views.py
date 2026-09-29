from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import Invoice, Return, Shift
from .returns import create_return
from .serializers import InvoiceSerializer, ReturnSerializer, ShiftSerializer
from .shifts import close_shift, open_shift


class ReturnView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "process_returns"

    def post(self, request):
        invoice = Invoice.objects.filter(id=request.data.get("invoice"), shop=request.shop).first()
        branch = request.shop.branches.filter(id=request.data.get("branch"), is_active=True).first()
        if not invoice or not branch:
            return Response({"code": "invalid_return"}, status=400)
        try:
            returned = create_return(shop=request.shop, invoice=invoice, branch=branch, items=request.data.get("items", []), reason=request.data.get("reason", ""), refund_amount=request.data.get("refund_amount", 0), actor=request.user, request=request)
        except (KeyError, TypeError, ValueError) as exc:
            return Response({"code": "invalid_return", "message": str(exc)}, status=400)
        return Response(ReturnSerializer(returned).data, status=201)


class ShiftView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_shifts"

    def get(self, request):
        return Response(ShiftSerializer(Shift.objects.filter(cashier=request.user).order_by("-opened_at")[:100], many=True).data)

    def post(self, request):
        branch = request.shop.branches.filter(id=request.data.get("branch"), is_active=True).first()
        if not branch:
            return Response({"code": "invalid_branch"}, status=400)
        try:
            shift = open_shift(shop=request.shop, branch=branch, cashier=request.user, opening_cash=request.data.get("opening_cash", 0), actor=request.user, request=request)
        except ValueError as exc:
            return Response({"code": "shift_error", "message": str(exc)}, status=400)
        return Response(ShiftSerializer(shift).data, status=201)


class ShiftCloseView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_shifts"

    def post(self, request, shift_id):
        shift = Shift.objects.filter(id=shift_id, cashier=request.user).first()
        if not shift:
            return Response({"code": "shift_not_found"}, status=404)
        try:
            shift = close_shift(shop=request.shop, shift=shift, closing_cash=request.data.get("closing_cash", 0), actor=request.user, request=request)
        except ValueError as exc:
            return Response({"code": "shift_error", "message": str(exc)}, status=400)
        return Response(ShiftSerializer(shift).data)
