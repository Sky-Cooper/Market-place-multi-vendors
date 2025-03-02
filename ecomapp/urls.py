from django.urls import path, include
from rest_framework import routers
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductImagesViewSet,
    CartOrderViewSet,
    CartOrderItemViewSet,
    ProductReviewViewSet,
    WishlistViewSet,
    AddressViewSet,
    ShoppingCartViewSet,
    CartItemViewSet,
    GlobalCartViewset,
)

from userauths.views import VendorViewSet, ClientViewSet


router = routers.DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("product-images", ProductImagesViewSet, basename="product-image")
router.register("cart-orders", CartOrderViewSet, basename="cart-order")
router.register("cart-order-items", CartOrderItemViewSet, basename="cart-order-item")
router.register("products-reviews", ProductReviewViewSet, basename="product-review")
router.register("wish-lists", WishlistViewSet, basename="wish-list")
router.register("addresses", AddressViewSet, basename="address")
router.register("shopping-carts", ShoppingCartViewSet, basename="shopping-cart")
router.register("cart-items", CartItemViewSet, basename="cart-item")
router.register("vendor/register", VendorViewSet, basename="vendor-register")
router.register("client/register", ClientViewSet, basename="client-register")
router.register("global/order", GlobalCartViewset, basename="global-order")
urlpatterns = [
    path("", include(router.urls)),
]
