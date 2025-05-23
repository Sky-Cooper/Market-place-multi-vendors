from django_filters import rest_framework as filters
from .models import Product, FoodProduct, Category, SubCategory, CartItem
from rest_framework.pagination import PageNumberPagination


class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_description = "page_size"
    max_page_size = 100
    page_query_params = "page"


class CartItemFilter(filters.FilterSet):
    is_ordered = filters.BooleanFilter(field_name="is_ordered")

    class Meta:
        model = CartItem
        fields = ["is_ordered"]


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    sector = filters.CharFilter(
        field_name="sub_category__category__sector__title", lookup_expr="icontains"
    )
    category = filters.CharFilter(
        field_name="sub_category__category__title", lookup_expr="icontains"
    )
    sub_category = filters.CharFilter(
        field_name="sub_category__title", lookup_expr="iexact"
    )
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    city = filters.CharFilter(field_name="vendor__city", lookup_expr="iexact")
    id = filters.NumberFilter(field_name="id", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["vendor", "in_stock"]


class FoodProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    sector = filters.CharFilter(
        field_name="sub_category__category__sector__title", lookup_expr="icontains"
    )
    category = filters.CharFilter(
        field_name="sub_category__category__title", lookup_expr="icontains"
    )
    sub_category = filters.CharFilter(
        field_name="sub_category__title", lookup_expr="iexact"
    )
    city = filters.CharFilter(field_name="vendor__city", lookup_expr="iexact")
    id = filters.NumberFilter(field_name="id", lookup_expr="iexact")

    class Meta:
        model = FoodProduct
        fields = ["vendor", "in_stock", "is_vegan"]


class CategoryFilter(filters.FilterSet):
    sector = filters.CharFilter(field_name="sector__title", lookup_expr="icontains")
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = Category
        fields = ["title", "sector"]


class SubCategoryFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr="icontains")
    category = filters.CharFilter(field_name="category__title", lookup_expr="icontains")
    sector = filters.CharFilter(
        field_name="category__sector__title", lookup_expr="icontains"
    )

    class Meta:
        model = SubCategory
        fields = ["title", "category", "sector"]
