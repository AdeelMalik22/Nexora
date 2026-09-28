from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import HasShopPermission

from .models import Barcode, Category, Price, PriceList, Product, ProductVariant, TaxCategory, Unit
from .serializers import (
    BarcodeSerializer,
    CategorySerializer,
    PriceListSerializer,
    PriceSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    TaxCategorySerializer,
    UnitSerializer,
)


class TenantCRUDView(APIView):
    permission_classes = (IsAuthenticated, HasShopPermission)
    required_permission = "manage_catalog"
    model = None
    serializer_class = None

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(shop=request.shop)
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)


class CategoryView(TenantCRUDView):
    model, serializer_class = Category, CategorySerializer


class UnitView(TenantCRUDView):
    model, serializer_class = Unit, UnitSerializer


class TaxCategoryView(TenantCRUDView):
    model, serializer_class = TaxCategory, TaxCategorySerializer


class ProductView(TenantCRUDView):
    model, serializer_class = Product, ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related("category", "unit", "tax_category").prefetch_related("variants")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        return queryset


class VariantView(TenantCRUDView):
    model, serializer_class = ProductVariant, ProductVariantSerializer


class BarcodeView(TenantCRUDView):
    model, serializer_class = Barcode, BarcodeSerializer

    def get(self, request):
        code = request.query_params.get("code")
        queryset = self.get_queryset().filter(code=code) if code else self.get_queryset()
        return Response(self.serializer_class(queryset.select_related("product", "variant"), many=True).data)


class PriceListView(TenantCRUDView):
    model, serializer_class = PriceList, PriceListSerializer


class PriceView(TenantCRUDView):
    model, serializer_class = Price, PriceSerializer
