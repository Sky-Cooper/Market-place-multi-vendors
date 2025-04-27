from django.contrib import admin
from ecomapp.models import (
    Category,
    Product,
    CartOrder,
    CartOrderItem,
    Wishlist,
    ProductImages,
    ProductReview,
    Address,
    ShoppingCart,
    CartItem,
    GlobalOrder,
    SubCategory,
    Subscription,
    SubscriptionFeature,
    SubscriptionPayment,
    SubscriptionPlan,
    ClaimedOrder,
    DeliveryAgentStrike,
    DeliveryRating,
    Sector,
    SubCategoryTag,
    VendorStrike,
    ClientStrike,
    Notification,
)


class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages


# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ["title", "category_image"]


# class CartOrderAdmin(admin.ModelAdmin):
#     list_display = [
#         "client",
#         "vendor",
#         "total_payed",
#         "paid_status",
#         "order_date",
#         "order_status",
#         "payment_method",
#         "global_order",
#     ]


# class CartOrderItemAdmin(admin.ModelAdmin):
#     list_display = [
#         "order",
#         "cart_item",
#         "facture",
#         "quantity",
#         "total_payed",
#         "is_delivered",
#     ]


# class ProductReviewAdmin(admin.ModelAdmin):
#     list_display = ["client", "product", "rating", "comment"]


# class WishlistAdmin(admin.ModelAdmin):

#     list_display = ["client", "products_count"]
#     filter_horizontal = ("products",)

#     def products_count(self, obj):
#         return obj.products.count()

#     products_count.short_description = "Total products"


# class AdressAdmin(admin.ModelAdmin):
#     list_display = ["user", "address", "status"]


# class ShoppingCartAdmin(admin.ModelAdmin):
#     list_display = ["client"]


# class CartItemAdmin(admin.ModelAdmin):
#     list_display = [
#         "shopping_cart",
#         "product",
#         "quantity",
#         "total_price",
#         "is_active",
#         "created_at",
#         "updated_at",
#     ]
admin.site.register(VendorStrike)
admin.site.register(ClientStrike)
admin.site.register(Notification)
admin.site.register(ClaimedOrder)
admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
admin.site.register(SubscriptionPayment)
admin.site.register(SubscriptionFeature)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(CartOrder)
admin.site.register(CartOrderItem)
admin.site.register(Wishlist)
admin.site.register(ProductReview)
admin.site.register(Address)
admin.site.register(ShoppingCart)
admin.site.register(CartItem)
admin.site.register(GlobalOrder)
admin.site.register(SubCategory)
admin.site.register(DeliveryRating)
admin.site.register(DeliveryAgentStrike)
admin.site.register(Sector)
admin.site.register(SubCategoryTag)
