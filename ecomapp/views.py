from django.shortcuts import render
from .models import *
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImagesSerializer,
    CartOrderSerializer,
    CartOrderItemSerializer,
    ProductReviewSerializer,
    WishlistSerializer,
    AddressSerializer,
    ShoppingCartSerializer,
    CartItemReadSerializer,
    CartItemWriteSerializer,
    SubCategorySerializer,
    GlobalOrderSerializer,
    SubscriptionFeatureSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    ClaimOrderSerializer,
    DeliveryRatingSerializer,
    DeliveryAgentStrikeSerializer,
    SectorSerializer,
    ClientStrikeSerializer,
    VendorStrikeSerializer,
    NotificationSerializer,
    FoodProductSerializer,
    TestimonialSerializer,
    ProductSizeSerializer,
    AiMessageSerializer,
    TopProductSerializer,
    SalesOverTimeSerializer,
    TopFoodProductsSerializer,
    StockAlertSerializer,
)
from collections import defaultdict
from rest_framework import viewsets, permissions, status
from django.db import transaction
from datetime import datetime, timedelta
from .prompts import identify_subcategories, select_products
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from userauths.models import *
from userauths.permissions import (
    IsOwnerOrSuperAdmin,
    RoleBasedQuerysetMixin,
    IsVendorOrClient,
)
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q, Sum
from .filters import (
    ProductFilter,
    FoodProductFilter,
    CategoryFilter,
    SubCategoryFilter,
    ProductPagination,
    CartItemFilter,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters as drf_filters
import os
from .available_data import SUBCATEGORIES, SUBCATEGORIES_PRODUCTS
from django.db.models import (
    Count,
    ExpressionWrapper,
    DecimalField,
    F,
    Value,
    Subquery,
    OuterRef,
    FloatField,
)
from rest_framework.permissions import IsAuthenticated


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can access this resource")
        serializer.save()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can create categories")
        print("Validated data", serializer.validated_data)
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can update categories")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can delete a category")
        return instance.delete()


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(
        detail=False,
        methods=["get"],
        url_path="trending",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def trending_products(self, request):
        trending_product = (
            Product.objects.filter(
                cart_items__cart_order_items__order__order_status="delivered"
            )
            .annotate(
                total_quantity_sold=Sum(
                    "cart_items__quantity",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    ),
                )
            )
            .order_by("-total_quantity_sold")[:10]
        )

        serializer = self.get_serializer(
            trending_product, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="top-products",
        permission_classes=[IsAuthenticated],
    )
    def top_products(self, request):

        user = request.user

        if not (hasattr(user, "vendor") or user.is_superuser):
            raise ValidationError(
                "only vendors or super users that can access this resource"
            )

        if user.is_superuser:
            vendor_id = request.data.get("vendor")
            if not vendor_id:
                raise ValidationError("As a super user you must provide a vendor ID")

            try:
                vendor = Vendor.objects.get(id=vendor_id)
            except Vendor.DoesNotExist:
                raise ValidationError("Vendor with the provided ID does not exist")
        else:
            vendor = user.vendor

        if vendor.field == "Food_Products":
            raise ValidationError(
                "this endpoint is for products and the vendor publishes food products"
            )

        days = int(request.data.get("days", 7))
        limit = int(request.data.get("limit", 10))

        since_date = timezone.now() - timedelta(days=days)
        compared_end_date = since_date
        compared_start_date = since_date - timedelta(days=days)
        products = (
            Product.objects.filter(
                vendor=vendor,
                cart_items__cart_order_items__order__order_status="delivered",
                cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_quantity_sold=Sum(
                    "cart_items__quantity",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
                total_orders=Count(
                    "cart_items__cart_order_items__order",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                    distinct=True,
                ),
                total_earned=ExpressionWrapper(
                    F("price")
                    * Sum(
                        "cart_items__quantity",
                        filter=Q(
                            cart_items__cart_order_items__order__order_status="delivered"
                        )
                        & Q(
                            cart_items__cart_order_items__order__order_date__gte=since_date
                        ),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("-total_quantity_sold")[:limit]
        )

        aggregates = CartOrder.objects.filter(
            vendor=vendor,
            order_date__gte=since_date,
            order_status="delivered",
        ).aggregate(total_delivered_orders=Count("id"), total_earned=Sum("total_payed"))

        total_delivered_orders = aggregates["total_delivered_orders"]
        total_earned = (aggregates["total_earned"] or 0) - (total_delivered_orders * 20)

        compared_aggregates = CartOrder.objects.filter(
            vendor=vendor,
            order_date__gte=compared_start_date,
            order_date__lte=compared_end_date,
            order_status="delivered",
        ).aggregate(total_delivered_orders=Count("id"), total_earned=Sum("total_payed"))

        compared_total_delivered_orders = compared_aggregates["total_delivered_orders"]
        compared_total_earned = compared_aggregates["total_earned"] or 0

        average_order_value = (
            total_earned / total_delivered_orders if total_delivered_orders > 0 else 0
        )
        compared_average_order_value = (
            compared_total_earned / compared_total_delivered_orders
            if compared_total_delivered_orders > 0
            else 0
        )

        top_category = (
            Category.objects.filter(
                sub_categories__products__vendor=vendor,
                sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_sold=Sum(
                    "sub_categories__products__cart_items__quantity",
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
                total_earned=Sum(
                    ExpressionWrapper(
                        F("sub_categories__products__cart_items__quantity")
                        * F("sub_categories__products__price"),
                        output_field=DecimalField(),
                    ),
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
            )
            .order_by("-total_sold")
            .first()
        )

        total_quantity_sold_based_on_limit = sum(
            [p.total_quantity_sold for p in products]
        )
        top_category_percentage = (
            (top_category.total_sold / total_quantity_sold_based_on_limit) * 100
            if total_quantity_sold_based_on_limit > 0
            else 0
        )

        sales_over_time = CartOrder.objects.filter(
            vendor=vendor,
            order_status="delivered",
            order_date__gte=since_date,
        ).annotate(
            total_earned=ExpressionWrapper(
                F("total_payed") - Value(20),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
        for order in sales_over_time:
            print("Order ID:", order.id)
            print("Total Payed:", order.total_payed)
            print("Total Earned:", getattr(order, "total_earned", "❌ NOT SET"))

        sales_over_time_serializer = SalesOverTimeSerializer(
            sales_over_time, many=True, context={"request": request}
        )
        print(
            "heree is teh serializerd data of ssales over time",
            sales_over_time_serializer.data,
        )

        category_sales = (
            Category.objects.filter(
                sub_categories__products__vendor=vendor,
                sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_sold=Sum(
                    "sub_categories__products__cart_items__quantity",
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                )
            )
            .values("title", "total_sold")
        )

        total_quantity_sold = sum(cat["total_sold"] or 0 for cat in category_sales)

        raw_distribution = [
            {
                "category": cat["title"],
                "percentage": (
                    round((cat["total_sold"] / total_quantity_sold) * 100, 2)
                    if total_quantity_sold
                    else 0
                ),
            }
            for cat in category_sales
        ]

        main_cats = []

        others_percentage = 0

        for cat in raw_distribution:
            if cat["percentage"] >= 8:
                main_cats.append(cat)

            else:
                others_percentage += cat["percentage"]

        if others_percentage > 0:
            main_cats.append(
                {"category": "Others", "percentage": round(others_percentage, 2)}
            )

        serializer = TopProductSerializer(
            products, many=True, context={"request": request}
        )
        serialized_products = serializer.data

        response_data = {
            "orders": {
                "total_delivered_orders": total_delivered_orders,
                "compared_total_delivered_orders": compared_total_delivered_orders,
            },
            "earnings": {
                "total_earned": total_earned,
                "compared_total_earned": compared_total_earned,
            },
            "AOV": {
                "average_order_value": average_order_value,
                "compared_average_order_value": compared_average_order_value,
            },
            "top_category": {
                "title": top_category.title if top_category else None,
                "total_sold": top_category.total_sold if top_category else 0,
                "total_earned": top_category.total_earned if top_category else 0,
                "percentage": top_category_percentage,
            },
            "products": serialized_products,
            "sales_over_time": sales_over_time_serializer.data,
            "product_distribution_on_categories": main_cats,
        }

        return Response(response_data)

    @action(
        detail=False,
        methods=["post"],
        url_path="stock-alert",
        permission_classes=[IsAuthenticated],
    )
    def stock_alert(self, request):
        user = request.user

        if not (hasattr(user, "vendor") or user.is_superuser):
            raise ValidationError(
                "only vendors or super users that can access this resource"
            )

        if user.is_superuser:
            vendor_id = request.data.get("vendor")
            if not vendor_id:
                raise ValidationError(
                    "as a super user you have to provide the vendor id"
                )

            try:
                vendor = Vendor.objects.get(id, vendor_id)

            except Vendor.DoesNotExist:
                raise ValidationError(
                    "a vendor with this id does not exist in the database"
                )

        else:
            vendor = user.vendor

        if vendor.field == "Food_Products":
            raise ValidationError(
                "this endpoint is for products and the vendor publishes food products"
            )

        days = int(request.data.get("days", 30))
        limit = int(request.data.get("limit", 10))
        print(f"days is here {days}")

        since_date = timezone.now() - timedelta(days=days)

        latest_order_date_subquery = Subquery(
            CartOrderItem.objects.filter(cart_item__product=OuterRef("pk"))
            .order_by("-created_at")
            .values("created_at")[:1]
        )

        products = (
            Product.objects.filter(vendor=vendor)
            .annotate(
                total_sold=Sum(
                    "cart_items__quantity",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
            )
            .annotate(
                average_sales=ExpressionWrapper(
                    F("total_sold") / Value(days), output_field=FloatField()
                ),
            )
            .annotate(
                days_left=ExpressionWrapper(
                    F("quantity") / F("average_sales") + Value(0.01),
                    output_field=FloatField(),
                ),
                last_order_date=latest_order_date_subquery,
            )
            .order_by("-total_sold")[:limit]
        )

        serializer = StockAlertSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "trending_products"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):

        user = self.request.user

        if not hasattr(user, "vendor"):
            raise ValidationError("No vendor is linked to this user.")
        vendor = user.vendor
        serializer.save(vendor=vendor)

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_superuser:
            serializer.save()
            return

        if not hasattr(user, "vendor"):
            raise ValidationError("No vendor is linked to this user.")

        vendor = user.vendor

        product = serializer.instance

        if product.vendor != vendor:
            raise ValidationError(
                "you cannot update this product because it belongs to another vendor"
            )

        serializer.save(vendor=vendor)

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_superuser:
            return instance.delete()

        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can delete the products")

        if instance.vendor != user.vendor:
            raise ValidationError(
                "you are not the owner of this product , you dont have the permission to delete it"
            )

        return instance.delete()


class FoodProductViewSet(viewsets.ModelViewSet):
    queryset = FoodProduct.objects.all()
    serializer_class = FoodProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(
        detail=False,
        methods=["get"],
        url_path="trending",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def trending_food_products(self, request):
        trending_food_product = (
            FoodProduct.objects.filter(
                cart_items__cart_order_items__order__order_status="delivered"
            )
            .annotate(
                total_quantity_sold=Sum(
                    "cart_items__quantity",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    ),
                )
            )
            .order_by("-total_quantity_sold")[:10]
        )
        serializer = self.get_serializer(
            trending_food_product, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="top-food-products",
        permission_classes=[IsAuthenticated],
    )
    def top_food_products(self, request):

        user = request.user

        if not (hasattr(user, "vendor") or user.is_superuser):
            raise ValidationError(
                "only vendors or super users that can access this resource"
            )

        if user.is_superuser:
            vendor_id = request.query_params.get("vendor")

            if not vendor_id:
                raise ValidationError("As a super user you must provide the vendor ID")

            try:
                vendor = Vendor.objects.get(id=vendor_id)

            except Vendor.DoesNotExist:
                raise ValidationError("vendor with the provided ID does not exist")

        else:
            vendor = user.vendor

        if vendor.field == "Products":
            raise ValidationError(
                "this endpoint is for food products and the vendor publishes products"
            )

        days = int(request.data.get("days", 7))
        limit = int(request.data.get("limit", 10))

        since_date = timezone.now() - timedelta(days=days)

        compared_end_date = since_date
        compared_start_date = since_date - timedelta(days=days)

        food_products = (
            FoodProduct.objects.filter(
                vendor=vendor,
                cart_items__cart_order_items__order__order_status="delivered",
                cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_quantity_sold=Sum(
                    "cart_items__quantity",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
                total_orders=Count(
                    "cart_items__cart_order_items__order",
                    filter=Q(
                        cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                    distinct=True,
                ),
                total_earned=ExpressionWrapper(
                    F("price")
                    * Sum(
                        "cart_items__quantity",
                        filter=Q(
                            cart_items__cart_order_items__order__order_status="delivered"
                        )
                        & Q(
                            cart_items__cart_order_items__order__order_date__gte=since_date
                        ),
                    ),
                    output_field=DecimalField(),
                ),
            )
            .order_by("-total_quantity_sold")[:limit]
        )

        aggregates = CartOrder.objects.filter(
            vendor=vendor,
            order_date__gte=since_date,
            order_status="delivered",
        ).aggregate(total_delivered_orders=Count("id"), total_earned=Sum("total_payed"))

        total_delivered_orders = aggregates["total_delivered_orders"]
        total_earned = aggregates["total_earned"]

        compared_aggregates = CartOrder.objects.filter(
            vendor=vendor,
            order_date__gte=compared_start_date,
            order_date__lte=compared_end_date,
            order_status="delivered",
        ).aggregate(total_delivered_orders=Count("id"), total_earned=Sum("total_payed"))

        compared_total_delivered_orders = compared_aggregates["total_delivered_orders"]
        compared_total_earned = compared_aggregates["total_earned"]

        average_order_value = (
            total_earned / total_delivered_orders if total_delivered_orders > 0 else 0
        )

        compared_average_order_value = (
            compared_total_earned / compared_total_delivered_orders
            if compared_total_delivered_orders > 0
            else 0
        )

        top_category = (
            Category.objects.filter(
                sub_categories__products__vendor=vendor,
                sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_sold=Sum(
                    "sub_categories__products__cart_items__quantity",
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
                total_earned=Sum(
                    ExpressionWrapper(
                        F("sub_categories__products__price")
                        * F("sub_categories__products__cart_items__quantity"),
                        output_field=DecimalField(),
                    ),
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                ),
            )
            .order_by("-total_sold")
            .first()
        )

        total_quantity_sold_based_on_limit = sum(
            [p.total_quantity_sold for p in food_products]
        )
        top_category_percentage = (
            (top_category.total_sold / total_quantity_sold_based_on_limit) * 100
            if total_quantity_sold_based_on_limit > 0
            else 0
        )

        sales_over_time = CartOrder.objects.filter(
            vendor=vendor,
            order_status="delivered",
            order_date__gte=since_date,
        )

        sales_over_time_serializer = SalesOverTimeSerializer(
            sales_over_time, many=True, context={"request": request}
        )

        category_sales = (
            Category.objects.filter(
                sub_categories__products__vendor=vendor,
                sub_categories__products__cart_items__cart_order_items__order__order_status="delivered",
                sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date,
            )
            .annotate(
                total_sold=Sum(
                    "sub_categories__products__cart_items__quantity",
                    filter=Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_status="delivered"
                    )
                    & Q(
                        sub_categories__products__cart_items__cart_order_items__order__order_date__gte=since_date
                    ),
                )
            )
            .values("title", "total_sold")
        )

        total_quantity_sold = sum(c["total_sold"] or 0 for c in category_sales)

        raw_distribution = [
            {
                "category": cat["title"],
                "percentage": (
                    round((cat["total_sold"] / total_quantity_sold) * 100, 2)
                    if total_quantity_sold
                    else 0
                ),
            }
            for cat in category_sales
        ]

        main_cats = []
        others_percentage = 0
        for cat in raw_distribution:
            if cat["percentage"] >= 8:
                main_cats.append(cat)

            else:
                others_percentage += cat["percentage"]

        if others_percentage > 0:
            main_cats.append(
                {"category": "Others", "percentage": round(others_percentage, 2)}
            )

        serializer = TopFoodProductsSerializer(
            food_products, many=True, context={"request": request}
        )

        response_data = {
            "orders": {
                "total_delivered_orders": total_delivered_orders,
                "compared_total_delivered_orders": compared_total_delivered_orders,
            },
            "earnings": {
                "total_earned": total_earned,
                "compared_total_earned": compared_total_earned,
            },
            "AOV": {
                "average_order_value": average_order_value,
                "compared_average_order_value": compared_average_order_value,
            },
            "food_products": serializer.data,
            "top_category": {
                "title": top_category.title if top_category else None,
                "total_sold": top_category.total_sold if top_category else 0,
                "total_earned": top_category.total_earned if top_category else 0,
                "percentage": top_category_percentage,
            },
            "sales_over_time": sales_over_time_serializer.data,
            "food_products_distribution_on_categories": main_cats,
        }

        return Response(response_data)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "trending_food_products"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "vendor"):
            raise ValidationError("No vendor is linked to this user")
        vendor = user.vendor
        serializer.save(vendor=vendor)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_superuser:
            serializer.save()
            return

        if not hasattr(user, "vendor"):
            raise ValidationError("No vendor is linked to this user")

        vendor = user.vendor
        food_product = serializer.instance
        if food_product.vendor != vendor:
            raise ValidationError(
                "you cannot update this product because it belongs to another vendor"
            )

        serializer.save(vendor=vendor)

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_superuser:
            return instance.delete()
        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors that can delete the products")

        if instance.vendor != user.vendor:
            raise ValidationError(
                "you are no the owner of this product, you dont have permissions to delete it"
            )

        return instance.delete()


class ProductImagesViewSet(viewsets.ModelViewSet):
    queryset = ProductImages.objects.all()
    serializer_class = ProductImagesSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can perform this operations")

        vendor = user.vendor

        product = serializer.validated_data.get("product")
        if product.vendor != vendor:
            raise ValidationError("you are not the owner of this product")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can perform this operation")
        vendor = user.vendor
        product = serializer.validated_data.get("product")
        if product.vendor != vendor:
            raise ValidationError("you are not the owner of this product")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_superuser:
            return instance.delete()

        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can delete product images")

        if instance.vendor != user.vendor:
            raise ValidationError(
                "you dont have the permission in order to delete this product image"
            )

        return instance.delete()


class CartOrderViewSet(viewsets.ModelViewSet):
    serializer_class = CartOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "client"):
            return CartOrder.objects.filter(client=user.client).order_by("-order_date")

        if hasattr(user, "vendor"):
            return CartOrder.objects.filter(vendor=user.vendor).order_by("-order_date")
        if user.is_superuser:
            return CartOrder.objects.all()

        return CartOrder.objects.none()


class CartOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CartOrderItem.objects.all()
        if hasattr(user, "vendor"):
            return CartOrderItem.objects.filter(order__vendor=user.vendor).order_by(
                "-created_at"
            )

        if hasattr(user, "client"):
            return CartOrderItem.objects.filter(order__client=user.client).order_by(
                "-created_at"
            )


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise ValidationError("Only clients can create reviews.")
        serializer.save(client=user.client)

    def perform_destroy(self, instance):
        user = self.request.user
        if not hasattr(user, "client") or user.client != instance.client:
            raise PermissionDenied("You cannot delete this review.")
        instance.delete()


class WishlistViewSet(viewsets.ModelViewSet):

    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Wishlist.objects.all()
        if hasattr(user, "client"):
            return Wishlist.objects.filter(client=user.client)
        return Wishlist.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise PermissionDenied("only clients who can have a wish list")
        if Wishlist.objects.filter(client=user.client).exists():
            raise ValidationError("this client has already a wishlist")
        serializer.save(client=user.client)

    @action(detail=False, methods=["post"])
    def add_product(self, request):
        user = request.user

        if not hasattr(user, "client"):
            return Response({"detail": "Only clients can have wishlists."}, status=403)

        try:
            wishlist = user.client.wishlist
        except Wishlist.DoesNotExist:
            return Response({"detail": "Wishlist not found."}, status=404)

        product_id = request.data.get("product_id")
        food_product_id = request.data.get("food_product_id")

        if not product_id and not food_product_id:
            return Response(
                {"detail": "Provide at least product_id or food_product_id."},
                status=400,
            )

        response_data = {}

        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                if not wishlist.products.filter(id=product.id).exists():
                    wishlist.products.add(product)
                    response_data["status"] = "Product added."
                    response_data["product"] = ProductSerializer(
                        product, context={"request": request}
                    ).data
                else:
                    response_data["status"] = "Product already in wishlist."
            except Product.DoesNotExist:
                response_data["status"] = "Invalid product_id."

        if food_product_id:
            try:
                food_product = FoodProduct.objects.get(id=food_product_id)
                if not wishlist.food_products.filter(id=food_product.id).exists():
                    wishlist.food_products.add(food_product)
                    response_data["status"] = "Food product added."
                    response_data["food_product"] = FoodProductSerializer(
                        food_product, context={"request": request}
                    ).data
                else:
                    response_data["status"] = "Food product already in wishlist."
            except FoodProduct.DoesNotExist:
                response_data["status"] = "Invalid food_product_id."

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def delete_product(self, request):
        user = request.user

        if not hasattr(user, "client"):
            return Response({"detail": "Only clients can have wishlists."}, status=403)

        try:
            wishlist = user.client.wishlist
        except Wishlist.DoesNotExist:
            return Response({"detail": "Wishlist not found."}, status=404)

        product_id = request.data.get("product_id")
        food_product_id = request.data.get("food_product_id")

        if not product_id and not food_product_id:
            return Response(
                {"detail": "Provide at least product_id or food_product_id."},
                status=400,
            )

        response_data = {}

        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                if wishlist.products.filter(id=product.id).exists():
                    wishlist.products.remove(product)
                    response_data["status"] = "Product removed from wishlist."
                    response_data["product"] = ProductSerializer(
                        product, context={"request": request}
                    ).data
                else:
                    response_data["status"] = "Product was not in wishlist."
            except Product.DoesNotExist:
                response_data["status"] = "Invalid product_id."

        if food_product_id:
            try:
                food_product = FoodProduct.objects.get(id=food_product_id)
                if wishlist.food_products.filter(id=food_product.id).exists():
                    wishlist.food_products.remove(food_product)
                    response_data["status"] = "Food product removed from wishlist."
                    response_data["food_product"] = FoodProductSerializer(
                        food_product, context={"request": request}
                    ).data
                else:
                    response_data["status"] = "Food product was not in wishlist."
            except FoodProduct.DoesNotExist:
                response_data["status"] = "Invalid food_product_id."

        return Response(response_data, status=status.HTTP_200_OK)


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Address.objects.all()
        if not user.is_anonymous:
            return Address.objects.filter(user=user)
        return Address.objects.none()

    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.user:
            raise PermissionDenied("you are not the owner of this address")


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ShoppingCart.objects.all()

        if not hasattr(user, "client"):
            raise PermissionDenied("only clients who can get their shopping cart")
        return ShoppingCart.objects.filter(client=user.client)

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise ValidationError("only users who can have a shopping cart")

        client = user.client
        if ShoppingCart.objects.filter(client=client).exists():
            raise ValidationError("this client has already a shopping cart")

        serializer.save()


class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CartItemWriteSerializer
        return CartItemReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "client") and hasattr(user.client, "shopping_cart"):

            return CartItem.objects.filter(shopping_cart=user.client.shopping_cart)
        if user.is_superuser:
            return CartItem.objects.all()
        return CartItem.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise PermissionDenied("only clients can add items to the cart.")
        shopping_cart = user.client.shopping_cart
        not_ordered_cart_items = shopping_cart.cart_items.filter(is_ordered=False)
        if len(not_ordered_cart_items) > 9:
            raise ValidationError(
                "you cannot have more than 10 cart items in your shopping cart"
            )
        serializer.save(shopping_cart=shopping_cart)

    def perform_destroy(self, instance):
        user = self.request.user
        if not hasattr(user, "client"):
            raise PermissionDenied("only clients who can delete or create cart items")

        client = user.client
        if not hasattr(client, "shopping_cart"):
            raise ValidationError("this client has no shopping cart object")

        if client.shopping_cart != instance.shopping_cart:
            raise PermissionDenied("you are not the owner of this cart item")

        return instance.delete()

    # feature : use signals in order to track weather or not the product is out of stock , if so , deleted it from the shopping cart , cart item and the ordercartitem
    # document on how to integrate signals to acheive that
    # the ordercartItem is created after the user payed potentially therfore it should gather the client and the vendor in order to send the notif to the vendor
    # sending the facture in email or downloading it from the site feature
    # notify the client incase they forgot a product in the wishlist or in the shoppingcart incase the product is getting to be out of stock


class GlobalCartViewset(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = GlobalOrderSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        if not hasattr(user, "client"):
            raise ValidationError("only clients who have the permission to buy")
        client = user.client
        shopping_cart = client.shopping_cart
        today = timezone.now()
        cart_items = shopping_cart.cart_items.filter(is_ordered=False)
        if len(cart_items) < 1:
            return Response({"error": "Your shopping cart is empty."})
        global_order = serializer.save(shopping_cart=shopping_cart)

        not_delivered_orders = (
            CartOrderItem.objects.filter(
                order__client=client,
                created_at__gte=today - timedelta(days=30),
            )
            .filter(~Q(order__order_status="delivered"))
            .count()
        )

        if not_delivered_orders > 9:
            raise ValidationError(
                "you cant have more than 10 none delivered orders in the last 30 days"
            )

        print(f"number of cart items is : !!!!!!!! {cart_items.count()}")

        vendors = {}

        global_order_total_price = 0
        for cart_item in cart_items:
            vendor = (
                cart_item.product.vendor
                if cart_item.product
                else cart_item.food_product.vendor
            )
            if not vendor or vendor.city != client.city:
                raise ValidationError("Some cart items are not available in your city.")
            global_order_total_price += cart_item.total_price
            if vendor not in vendors:
                vendors[vendor] = []

            vendors[vendor].append(cart_item)

        cart_orders = []
        vendor_keys = list(vendors.keys())
        global_order.total_price = global_order_total_price + (len(vendor_keys) * 20)
        global_order.save(update_fields=["total_price"])

        try:
            for vendor, cart_items in vendors.items():

                total_payed = sum(cart_item.get_price() for cart_item in cart_items)

                cart_order = CartOrder.objects.create(
                    client=client,
                    vendor=vendor,
                    total_payed=(
                        total_payed + 20
                        if global_order.delivery_option
                        else total_payed
                    ),
                    payment_method="cod",
                    global_order=global_order,
                    delivery_option=global_order.delivery_option,
                )

                cart_order.save()

                print(f"Created CartOrder: {cart_order}")
                cart_orders.append(cart_order)

                for cart_item in cart_items:
                    try:
                        CartOrderItem.objects.create(
                            client=client,
                            order=cart_order,
                            cart_item=cart_item,
                            total_payed=(
                                cart_item.product.price
                                if cart_item.product
                                else cart_item.food_product.price
                            )
                            * cart_item.quantity,
                        )
                        cart_item.is_ordered = True
                        cart_item.save(update_fields=["is_ordered"])

                        print(
                            f"Created CartOrderItem for CartOrder ID: {cart_order.id}"
                        )
                    except Exception as e:
                        raise e
                    # TODO : make sure to use signals in order to inform the vendors and send updates in their email

        except Exception as e:
            raise e

        return Response(
            {
                "message": "global cart order is successfully created and implemented",
                "global_cart_id": global_order.id,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            global_orders = GlobalOrder.objects.all()
        if not hasattr(user, "client"):
            raise ValidationError("only clients that can access this resource")
        client = user.client
        if hasattr(user, "client"):
            global_orders = GlobalOrder.objects.filter(shopping_cart__client=client)

        serializer = GlobalOrderSerializer(
            global_orders, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can perform this method")

        return instance.delete()


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Subscription.objects.all()
        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can access this resource")

        return Subscription.objects.filter(vendor=user.vendor)


class SubscriptionFeatureViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionFeatureSerializer
    queryset = SubscriptionFeature.objects.all()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class SubscriptionPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SubscriptionPayment.objects.all()

        if not hasattr(user, "vendor"):
            raise ValidationError("only vendors who can access this resource")

        return SubscriptionPayment.objects.filter(subscription__vendor=user.vendor)


class ClaimedOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ClaimedOrder.objects.all()

        if hasattr(user, "delivery_agent"):
            print("user is delivery agent")
            return ClaimedOrder.objects.filter(delivery_agent=user.delivery_agent)

        if hasattr(user, "vendor"):
            return ClaimedOrder.objects.filter(
                order__vendor=user.vendor, is_failed=False
            )

        if hasattr(user, "client"):
            return ClaimedOrder.objects.filter(
                order__client=user.client, is_failed=False
            )

        return ClaimedOrder.objects.none()


class DeliveryRatingViewSet(viewsets.ModelViewSet):
    queryset = DeliveryRating.objects.all()
    serializer_class = DeliveryRatingSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        user = self.request.user
        if not hasattr(user, "client") and not user.is_superuser:
            raise ValidationError(
                "only clients and super users who are allowed to update a delivery rating"
            )

        return serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not hasattr(user, "client") and not user.is_superuser:
            raise ValidationError(
                "only clients who can delete or destroy related delivery rating objects, or superusers"
            )
        if hasattr(user, "client"):
            if user.client != instance.client:
                raise ValidationError(
                    "you are not the owner of this particular delivery rating object in order to delete it"
                )

        return instance.delete()


class DeliveryAgentStrikeViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryAgentStrikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return DeliveryAgentStrike.objects.all()

        if not hasattr(user, "delivery_agent"):
            raise PermissionDenied("only delivery agents who can access this resource")

        return DeliveryAgentStrike.objects.filter(delivery_agent=user.delivery_agent)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            raise PermissionError("only superusers or system can create strikes")
        serializer.save()


class VendorStrikeViewSet(viewsets.ModelViewSet):
    serializer_class = VendorStrikeSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return VendorStrike.objects.all()

        if not hasattr(user, "vendor"):
            raise PermissionDenied("only vendors who can access this resource")

        return VendorStrike.objects.filter(vendor=user.vendor)


class ClientStrikeViewSet(viewsets.ModelViewSet):
    serializer_class = ClientStrikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ClientStrike.objects.all()

        if not hasattr(user, "client"):
            raise PermissionDenied("only clients who can access this resource")

        return ClientStrike.objects.filter(client=user.client)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Notification.objects.all()

        return Notification.objects.filter(user=user)


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]


class ProductListAPIView(generics.ListAPIView):

    queryset = Product.objects.filter(is_active=True).select_related(
        "sub_category__category__sector", "vendor"
    )
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = [
        "title",
        "description",
        "tags__name",
        "specifications",
        "vendor_title",
        "vendor__user__first_name",
    ]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]


class FoodProductListAPIView(generics.ListAPIView):
    queryset = FoodProduct.objects.filter(is_active=True).select_related(
        "sub_categories__category__sector", "vendor"
    )
    serializer_class = FoodProductSerializer
    pagination_class = ProductPagination
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = FoodProductFilter
    search_fields = [
        "title",
        "description",
        "tags__name",
        "specifications",
        "vendor_title",
        "ingredients",
    ]
    ordering_fields = ["price", "created_at", "calories"]
    ordering = ["-created_at"]


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = CategoryFilter
    search_fields = ["title", "sector__title"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class SubCategoryListAPIView(generics.ListAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = SubCategoryFilter
    search_fields = ["title", "category__title", "category__sector__title"]

    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class ProductSizeView(viewsets.ModelViewSet):
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer

    def get_permissions(self):
        if self.action in ["retrieve", "list"]:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]


class CartItemListAPIView(generics.ListAPIView):
    serializer_class = CartItemReadSerializer
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = CartItemFilter
    pagination_class = ProductPagination
    search_fields = ["is_ordered"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser and not hasattr(user, "client"):
            raise ValidationError(
                "only super users and clients tht can access this resource"
            )
        if user.is_superuser:
            return CartItem.objects.all()

        return CartItem.objects.filter(shopping_cart=user.client.shopping_cart)


class AIProductAssistantAPIView(APIView):
    def post(self, request):
        print("Incoming request data:", request.data)
        serializer = AiMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data["message"]
        response = identify_subcategories(message, SUBCATEGORIES)

        if not response:
            return Response({"message": "No relevant subcategories found."}, status=200)
        print(f"response of first prompt is {response} ")

        desired_subcategories_with_products = {}
        for subcategory in response.values():
            normalized_sub = subcategory.title()
            if normalized_sub in SUBCATEGORIES_PRODUCTS:
                desired_subcategories_with_products[normalized_sub] = (
                    SUBCATEGORIES_PRODUCTS[normalized_sub]
                )

        if not desired_subcategories_with_products:
            return Response(
                {"message": "No products found for the relevant subcategories."},
                status=200,
            )

        desired_products = select_products(message, desired_subcategories_with_products)

        print(f"response of second prompt {desired_products}")
        products = []

        if desired_products:
            food_titles = desired_products.get("food_product", [])
            for title in food_titles:
                food_product = FoodProduct.objects.filter(title__iexact=title).first()
                if food_product:
                    products.append(
                        FoodProductSerializer(
                            food_product, context={"request": request}
                        ).data
                    )

            product_titles = desired_products.get("product", [])
            for title in product_titles:
                product = Product.objects.filter(title__iexact=title).first()
                if product:
                    products.append(
                        ProductSerializer(product, context={"request": request}).data
                    )

        if not products:
            return Response(
                {"message": "No products found in the databasse regarding your need"},
                status=200,
            )

        response_data = {"products": products}

        return Response(response_data, status=200)
