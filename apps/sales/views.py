from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission
from apps.catalog.models import Product, ProductVariant

from .models import Cart, CartItem, Invoice
from .serializers import CartItemSerializer, CartSerializer, InvoiceSerializer
from .services import finalize_cart


class CartView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "create_sale"

    def get(self, request):
        return Response(CartSerializer(Cart.objects.filter(cashier=request.user).prefetch_related("items"), many=True).data)

    def post(self, request):
        branch = request.shop.branches.filter(id=request.data.get("branch"), is_active=True).first()
        if branch is None:
            return Response({"code": "invalid_branch"}, status=400)
        customer = None
        if request.data.get("customer"):
            from apps.customers.models import Customer
            customer = Customer.objects.filter(id=request.data["customer"], shop=request.shop, is_active=True).first()
            if customer is None:
                return Response({"code": "invalid_customer"}, status=400)
        cart = Cart.objects.create(shop=request.shop, branch=branch, cashier=request.user, customer=customer)
        return Response(CartSerializer(cart).data, status=201)


class CartItemView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "create_sale"

    def post(self, request, cart_id):
        cart = Cart.objects.filter(id=cart_id, cashier=request.user, status__in=(Cart.Status.OPEN, Cart.Status.HELD)).first()
        if cart is None:
            return Response({"code": "cart_unavailable"}, status=404)
        product = Product.objects.unscoped().filter(id=request.data.get("product"), shop=request.shop).first() if request.data.get("product") else None
        variant = ProductVariant.objects.unscoped().filter(id=request.data.get("variant"), shop=request.shop).first() if request.data.get("variant") else None
        if (product is None) == (variant is None):
            return Response({"code": "one_target_required"}, status=400)
        item = CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=request.data["quantity"], unit_price=request.data["unit_price"], discount=request.data.get("discount", 0))
        return Response(CartItemSerializer(item).data, status=201)


class CartFinalizeView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "create_sale"

    def post(self, request, cart_id):
        try:
            invoice = finalize_cart(shop=request.shop, cart_id=cart_id, payments=request.data.get("payments", []), actor=request.user, request=request)
        except (KeyError, ValueError) as exc:
            return Response({"code": "checkout_failed", "message": str(exc)}, status=400)
        return Response(InvoiceSerializer(invoice).data, status=201)


class InvoiceView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "view_sales"

    def get(self, request):
        return Response(InvoiceSerializer(Invoice.objects.prefetch_related("items").order_by("-created_at")[:200], many=True).data)
