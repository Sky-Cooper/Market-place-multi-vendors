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
)


class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]

    def get_tags(self, obj):
        return ",".join(obj.tags.names())

    get_tags.short_description = "Tags"

    list_display = [
        "vendor",
        "title",
        "product_image",
        "price",
        "quantity",
        "discount_percentage",
        "category",
        "featured",
        "is_active",
        "get_tags",
    ]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "category_image"]


class CartOrderAdmin(admin.ModelAdmin):
    list_display = [
        "client",
        "vendor",
        "total_payed",
        "paid_status",
        "order_date",
        "order_status",
        "payment_method",
        "global_order",
    ]


class CartOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "cart_item",
        "facture",
        "quantity",
        "total_payed",
        "is_delivered",
    ]


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ["client", "product", "rating", "comment"]


class WishlistAdmin(admin.ModelAdmin):

    list_display = ["client", "products_count"]
    filter_horizontal = ("products",)

    def products_count(self, obj):
        return obj.products.count()

    products_count.short_description = "Total products"


class AdressAdmin(admin.ModelAdmin):
    list_display = ["user", "address", "status"]


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ["client"]


class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        "shopping_cart",
        "product",
        "quantity",
        "total_price",
        "is_active",
        "created_at",
        "updated_at",
    ]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)

admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Address, AdressAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(GlobalOrder)
