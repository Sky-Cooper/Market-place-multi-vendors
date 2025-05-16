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
    FoodProductViewSet,
    TestimonialViewSet,
    FoodProductListAPIView,
    ProductListAPIView,
)

from userauths.views import VendorViewSet, ClientViewSet, DeliveryAgentViewSet


router = routers.DefaultRouter()

router.register("testimonials", TestimonialViewSet, basename="testimonials")
router.register("food-products", FoodProductViewSet, basename="food-products")
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
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")
router.register("product-images", ProductImagesViewSet, basename="product-images")
router.register("cart-orders", CartOrderViewSet, basename="cart-orders")
router.register("cart-order-items", CartOrderItemViewSet, basename="cart-order-items")
router.register("products-reviews", ProductReviewViewSet, basename="product-reviews")
router.register("wish-lists", WishlistViewSet, basename="wish-lists")
router.register("addresses", AddressViewSet, basename="addresses")
router.register("shopping-carts", ShoppingCartViewSet, basename="shopping-carts")
router.register("cart-items", CartItemViewSet, basename="cart-items")
router.register("vendor/register", VendorViewSet, basename="vendor-register")
router.register("client/register", ClientViewSet, basename="client-register")
router.register(
    "delivery-agent/register", DeliveryAgentViewSet, basename="delivery-agent"
)
router.register("sub-categories", SubCategoryViewSet, basename="subcategories")

urlpatterns = [
    path("global-orders/", GlobalCartViewset.as_view(), name="global-orders"),
    path("products/list/", ProductListAPIView.as_view(), name="product-list-filtered"),
    path(
        "food-products/list/",
        FoodProductListAPIView.as_view(),
        name="food-product-list-filtered",
    ),
    path("", include(router.urls)),
]
