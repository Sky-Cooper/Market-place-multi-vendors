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
    CartItemSerializer,
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
)
from rest_framework import viewsets, permissions, status
from django.db import transaction
from datetime import datetime, timedelta

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
from .filters import ProductFilter, FoodProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters as drf_filters

# Create your views here.


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
            return CartOrder.objects.filter(client=user.client)

        if hasattr(user, "vendor"):
            return CartOrder.objects.filter(vendor=user.vendor)
        if user.is_superuser:
            return CartOrder.objects.all()

        return CartOrder.objects.none()


class CartOrderItemViewSet(viewsets.ModelViewSet):
    queryset = CartOrderItem.objects.all()
    serializer_class = CartOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorOrClient]
    # logically speaking if i understand , the cartorderviewset get created after the client payed the full price it should be created multiple cartorder depending on how many different vendors , and in each cartorder it should create caartorderitems

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CartOrderItem.objects.all()
        if hasattr(user, "vendor"):
            return CartOrderItem.objects.filter(order__vendor=user.vendor)

        if hasattr(user, "client"):
            return CartOrderItem.objects.filter(order__client=user.client)


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
    queryset = Wishlist.objects.all()
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
        serializer.save()

    @action(detail=True, methods=["post"])
    def add_product(self, request, pk=None):
        wish_list = self.get_object()
        product_id = request.data.get("product_id")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValidationError("a product with this id does not exist")

        if not wish_list.products.filter(id=product.id).exists():
            wish_list.products.add(product)
            return Response({"status": "Product added to wishlist"})
        return Response({"status": "Product already in the wishlist"})

    @action(detail=True, methods=["post"])
    def remove_product(self, request, pk=None):
        wish_list = self.get_object()
        product_id = request.data.get("product_id")
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ValidationError("a product with this id does not exist")

        if wish_list.products.filter(id=product.id).exists():
            wish_list.products.remove(product)
            return Response({"status": "product removed from the wishlist"})
        return Response({"status": "Product does not exist in the wishlist"})

        # create a wish list right after the user is signed up


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
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

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

        global_order.total_price = global_order_total_price
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
                    cart_item.save()

                    print(f"Created CartOrderItem for CartOrder ID: {cart_order.id}")
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
    serializer_class = ProductSerializer
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
        "sub_category__category__sector", "vendor"
    )
    serializer_class = FoodProductSerializer
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
