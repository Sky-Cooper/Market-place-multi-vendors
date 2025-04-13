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
)
from rest_framework import viewsets, permissions, status

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from userauths.models import *
from userauths.permissions import (
    IsOwnerOrSuperAdmin,
    RoleBasedQuerysetMixin,
    IsVendorOrClient,
)


# Create your views here.


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

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can update categories")

    def perform_destroy(self, instance):
        user = self.request.user
        if not user.is_superuser:
            raise ValidationError("only super users who can delete a category")


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
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

        instance.delete()


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

        instance.delete()


class CartOrderViewSet(viewsets.ModelViewSet):
    serializer_class = CartOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

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
            return [permissions.AllowAny]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise ValidationError("only clients who can create reviews")
        serializer.save(client=user.client)

    def perform_destroy(self, instance):
        user = self.request.user
        if not hasattr(user, "client"):
            raise PermissionDenied("this user has no client account")

        if user.client != instance.client:
            raise PermissionDenied(
                "you are not the owner of this review , you cannot delete it"
            )

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
        serializer.save(client=self.request.user)

        # create a wish list right after the user is signed up


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny]
        return [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Address.objects.all()
        return Address.objects.filter(user=user)

    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.user:
            raise PermissionDenied("you are not the owner of this adress")


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
        serializer.save(client=self.request.user.client)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "client") and hasattr(user.client, "shopping_cart"):
            return CartItem.objects.filter(shopping_cart=user.client.shopping_cart)
        if user.role == UserRoles.SUPER_ADMIN:
            return CartItem.objects.all()
        return CartItem.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "client"):
            raise PermissionDenied("only clients can add items to the cart.")
        shopping_cart = user.client.shopping_cart
        serializer.save(shopping_cart=shopping_cart)

    # feature : use signals in order to track weather or not the product is out of stock , if so , deleted it from the shopping cart , cart item and the ordercartitem
    # document on how to integrate signals to acheive that
    # the ordercartItem is created after the user payed potentially therfore it should gather the client and the vendor in order to send the notif to the vendor
    # sending the facture in email or downloading it from the site feature
    # notify the client incase they forgot a product in the wishlist or in the shoppingcart incase the product is getting to be out of stock


class GlobalCartViewset(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GlobalOrderSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        global_order = serializer.save()
        user = request.user
        if not hasattr(user, "client"):
            raise ValidationError("only clients who have the permission to buy")
        client = user.client
        shopping_cart = global_order.shopping_cart

        cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)
        if len(cart_items) < 1:
            return Response({"error": "there is no cart item for this shopping cart"})

        print(f"number of cart items is : !!!!!!!! {cart_items.count()}")

        vendors = {}

        for cart_item in cart_items:
            vendor = cart_item.product.vendor
            if vendor not in vendors:
                vendors[vendor] = []

            vendors[vendor].append(cart_item)

        cart_orders = []

        try:
            for vendor, cart_items in vendors.items():

                total_payed = sum(
                    cart_item.product.price * cart_item.quantity
                    for cart_item in cart_items
                )

                cart_order = CartOrder.objects.create(
                    client=client,
                    vendor=vendor,
                    total_payed=total_payed,
                    paid_status=True,
                    payment_method="online",
                    global_order=global_order,
                )

                cart_order.save()

                print(f"here is the cart_order id : {cart_order.oid}")

                print(f"Created CartOrder: {cart_order}")
                cart_orders.append(cart_order)

                for cart_item in cart_items:
                    CartOrderItem.objects.create(
                        client=client,
                        order=cart_order,
                        cart_item=cart_item,
                        quantity=cart_item.quantity,
                        total_payed=cart_item.product.price * cart_item.quantity,
                        product=cart_item.product,
                    )

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
        global_orders = GlobalOrder.objects.all()
        serializer = GlobalOrderSerializer(
            global_orders, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubCategory(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAdminUser]
