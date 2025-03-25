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
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

# Create your views here.


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):

        user = self.request.user

        try:
            vendor = user.vendor

        except Vendor.DoesNotExist:
            raise ValidationError(
                "there is no vender related to the current logged in  user : "
            )

        serializer.save(vendor=vendor)

    def perform_update(self, serializer):
        user = self.request.user

        if user.is_superuser:
            serializer.save()
            return

        try:
            vendor = user.vendor

        except Vendor.DoesNotExist:
            raise ValidationError(
                "there is no vender related to the current logged in user : "
            )

        product = serializer.instance

        if product.vendor != vendor:
            raise ValidationError(
                "you cannot update this product because it belongs to another vendor"
            )

        serializer.save()


class ProductImagesViewSet(viewsets.ModelViewSet):
    queryset = ProductImages.objects.all()
    serializer_class = ProductImagesSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save()


class CartOrderViewSet(viewsets.ModelViewSet):
    queryset = CartOrder.objects.all()
    serializer_class = CartOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartOrderItemViewSet(viewsets.ModelViewSet):
    queryset = CartOrderItem.objects.all()
    serializer_class = CartOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    # logically speaking if i understand , the cartorderviewset get created after the client payed the full price it should be created multiple cartorder depending on how many different vendors , and in each cartorder it should create caartorderitems


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        # create a wish list right after the user is signed up


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permissions_classes = [permissions.IsAuthenticated]


class ShoppingCartViewSet(viewsets.ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

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
