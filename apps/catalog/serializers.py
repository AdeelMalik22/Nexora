from rest_framework import serializers

from .models import Barcode, Category, Price, PriceList, Product, ProductVariant, TaxCategory, Unit


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "parent", "is_active")
        read_only_fields = ("id",)


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ("id", "name", "symbol", "precision")
        read_only_fields = ("id",)


class TaxCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxCategory
        fields = ("id", "name", "rate", "is_active")
        read_only_fields = ("id",)


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ("id", "product", "name", "sku", "attributes", "is_active")
        read_only_fields = ("id",)

    def validate_product(self, value):
        if value.shop_id != self.context["request"].shop.id:
            raise serializers.ValidationError("This product belongs to another shop.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "sku", "description", "category", "unit", "tax_category", "is_active", "variants")
        read_only_fields = ("id", "variants")

    def validate(self, attrs):
        shop = self.context["request"].shop
        for field in ("category", "unit", "tax_category"):
            value = attrs.get(field)
            if value is not None and value.shop_id != shop.id:
                raise serializers.ValidationError({field: "This resource belongs to another shop."})
        return attrs


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = ("id", "code", "product", "variant", "is_primary")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("variant"):
            raise serializers.ValidationError({"code": "A barcode must target a product or variant."})
        shop = self.context["request"].shop
        for field in ("product", "variant"):
            value = attrs.get(field)
            if value is not None and value.shop_id != shop.id:
                raise serializers.ValidationError({field: "This resource belongs to another shop."})
        return attrs


class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = ("id", "name", "currency", "is_default", "is_active")
        read_only_fields = ("id",)


class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ("id", "price_list", "product", "variant", "amount", "valid_from", "valid_until")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if not attrs.get("product") and not attrs.get("variant"):
            raise serializers.ValidationError({"price": "A price must target a product or variant."})
        shop = self.context["request"].shop
        for field in ("price_list", "product", "variant"):
            value = attrs.get(field)
            if value is not None and value.shop_id != shop.id:
                raise serializers.ValidationError({field: "This resource belongs to another shop."})
        return attrs
