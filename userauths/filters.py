from .models import Vendor
from django_filters import rest_framework as filters
from rest_framework.pagination import PageNumberPagination


class VendorPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


class VendorFilter(filters.FilterSet):
    city = filters.CharFilter(field_name="city", lookup_expr="icontains")

    class Meta:
        model = Vendor
        fields = ["city"]
