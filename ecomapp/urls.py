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
    SubCategoryViewSet,
    SubscriptionViewSet,
    SubscriptionFeatureViewSet,
    SubscriptionPaymentViewSet,
    SubscriptionPlanViewSet,
    ClaimedOrderViewSet,
    DeliveryAgentStrikeViewSet,
    DeliveryRatingViewSet,
    SectorViewSet,
    VendorStrikeViewSet,
    ClientStrikeViewSet,
    NotificationViewSet,
)

from userauths.views import VendorViewSet, ClientViewSet, DeliveryAgentViewSet


router = routers.DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notifications")
router.register("vendor-strikes", VendorStrikeViewSet, basename="vendor-strikes")
router.register("client-strikes", ClientStrikeViewSet, basename="client-strikes")
router.register("sectors", SectorViewSet, basename="sectors")
router.register("delivery-ratings", DeliveryRatingViewSet, basename="delivery-ratings")
router.register(
    "delivery-strikes",
    DeliveryAgentStrikeViewSet,
    basename="delivery-strikes",
)
router.register("claimed-orders", ClaimedOrderViewSet, basename="claimed-orders")
router.register("subscriptions", SubscriptionViewSet, basename="subscriptions")
router.register(
    "subscription-plans", SubscriptionPlanViewSet, basename="subscription-plan"
)
router.register(
    "subscription-payments",
    SubscriptionPaymentViewSet,
    basename="subscription-payments",
)
router.register(
    "subscription-features",
    SubscriptionFeatureViewSet,
    basename="subscription-features",
)
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("product-images", ProductImagesViewSet, basename="product-image")
router.register("cart-orders", CartOrderViewSet, basename="cart-orders")
router.register("cart-order-items", CartOrderItemViewSet, basename="cart-order-item")
router.register("products-reviews", ProductReviewViewSet, basename="product-review")
router.register("wish-lists", WishlistViewSet, basename="wish-list")
router.register("addresses", AddressViewSet, basename="address")
router.register("shopping-carts", ShoppingCartViewSet, basename="shopping-cart")
router.register("cart-items", CartItemViewSet, basename="cart-item")
router.register("vendor/register", VendorViewSet, basename="vendor-register")
router.register("client/register", ClientViewSet, basename="client-register")
router.register(
    "delivery-agent/register", DeliveryAgentViewSet, basename="delivery-agent"
)
router.register("sub-category", SubCategoryViewSet, basename="subcategory")
# router.register("global-order", GlobalCartViewset, basename="global-order")
urlpatterns = [
    path("", include(router.urls)),
    path("global-orders/", GlobalCartViewset.as_view(), name="global-orders"),
]
