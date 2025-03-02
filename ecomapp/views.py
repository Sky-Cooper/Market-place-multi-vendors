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
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError


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


class GlobalCartViewset(viewsets.ModelViewSet):
    queryset = GlobalOrder.objects.all()
    serializer_class = GlobalOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SubCategory(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAdminUser]
