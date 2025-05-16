from django_filters import rest_framework as filters
from .models import Product, FoodProduct


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    sector = filters.CharFilter(
        field_name="sub_category__category__sector__title", lookup_expr="iexact"
    )
    category = filters.CharFilter(
        field_name="sub_category__category__title", lookup_expr="iexact"
    )
    sub_category = filters.CharFilter(
        field_name="sub_category__title", lookup_expr="iexact"
    )

    class Meta:
        model = Product
        fields = ["vendor", "in_stock"]


class FoodProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    sector = filters.CharFilter(
        field_name="sub_category__category__sector__title", lookup_expr="iexact"
    )
    category = filters.CharFilter(
        field_name="sub_category__category__title", lookup_expr="iexact"
    )
    sub_category = filters.CharFilter(
        field_name="sub_category__title", lookup_expr="iexact"
    )

    class Meta:
        model = FoodProduct
        fields = ["vendor", "in_stock", "is_vegan"]
