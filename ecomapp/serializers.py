from rest_framework import serializers
from .models import *
from django.utils.html import mark_safe
from userauths.models import *
from taggit.serializers import TaggitSerializer, TagListSerializerField


class CategorySerializer(serializers.ModelSerializer):
    cid = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["cid", "title", "description", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


class ProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    pid = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    tags = TagListSerializerField()

    class Meta:
        model = Product
        fields = [
            "pid",
            "title",
            "description",
            "category",
            "old_price",
            "price",
            "tags",
            "is_digital",
            "image",
            "image_url",
            "specifications",
            "is_active",
            "in_stock",
            "featured",
            "discount_percentage",
            "quantity",
        ]

        read_only_fields = ["discount_percentage", "pid", "product_status", "vendor"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate_vendor(self, value):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "you cannot create a product because this current user has no vendor account"
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "this current logged in user has no vendor"
            )

        if user.vendor.is_banned:
            raise serializers.ValidationError("this vendor is banned")

        validated_data["vendor"] = user.vendor

        tags = validated_data.pop("tags", [])

        product = Product.objects.create(**validated_data)
        product.tags.add(*tags)

        return product

    def get_tags(self, obj):
        return list(obj.tags.names())


class ProductImagesSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ProductImages
        fields = ["image", "image_url", "product"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate_product(self, value):
        user = self.context["request"].user

        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "there is no vendor related to this current logged in user !"
            )

        if value.vendor != user.vendor:
            raise serializers.ValidationError(
                "you cannot add images to this product because it belongs to another vendor"
            )

        return value


class CartOrderSerializer(serializers.ModelSerializer):
    oid = serializers.ReadOnlyField()
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # vendor = serializers.PrimaryKeyRelatedField(
    #     queryset=Vendor.objects.all(), allow_null=True
    # )

    class Meta:
        model = CartOrder
        fields = [
            "oid",
            "vendor",
            "total_payed",
            "paid_status",
            "order_date",
            "order_status",
            "is_canceled",
            "payment_method",
        ]
        read_only_fields = [
            "vendor",
            "oid",
            "paid_status",
            "order_date",
            "order_status",
            "total_payed",
            "payment_method",
        ]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        data["client"] = user.client
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        validated_data["client"] = user.client
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if hasattr(user, "client"):
            if "is_canceled" in validated_data and instance.order_status != "delivered":
                instance.is_canceled = validated_data["is_canceled"]
                validated_data.pop("is_canceled")

            if "is_canceled" in validated_data and instance.order_status == "delivered":
                raise serializers.ValidationError(
                    "you can not cancel an order after being delivered"
                )

        if hasattr(user, "vendor"):
            if "order_status" in validated_data and not instance.is_canceled:
                instance.order_status = validated_data["order_status"]
                validated_data.pop("order_status")

            if "order_status" in validated_data and instance.is_canceled:
                raise serializers.ValidationError("you cannot update a canceled order")

        return super().update(instance, validated_data)

    # def validate(self, data):
    #     user = self.context["request"].user
    #     if not hasattr(user, "client"):
    #         raise serializers.ValidationError("this user has no client account")

    #     data["client"] = user.client

    #     return data

    # def create(self, validated_data):
    #     user = self.context["request"].user
    #     if not hasattr(user, "client"):
    #         raise serializers.ValidationError("this user has no client account")

    #     validated_data["client"] = user.client

    #     return super().create(validated_data)


class CartOrderItemSerializer(serializers.ModelSerializer):
    coiid = serializers.ReadOnlyField()
    order = serializers.PrimaryKeyRelatedField(queryset=CartOrder.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartOrderItem
        fields = [
            "coiid",
            "order",
            "product",
            "quantity",
            "total_payed",
            "is_canceled",
            "cart_order_item_status",
        ]
        read_only_fields = ["total_payed", "coiid", "facture"]

        # the facture and the total_price should be calculated and generated, (make sure to send the facture in the gmail , for later imporvments not now)

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "only clients who can create a cart order item"
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if hasattr(user, "client"):
            if validated_data.get("is_canceled", False):
                if (
                    instance.is_canceled
                    or instance.cart_order_item_status == "delivered"
                ):
                    raise serializers.ValidationError(
                        "Cannot cancel already delivered or canceled item."
                    )
                instance.is_canceled = True
                validated_data.pop("is_canceled")

        if hasattr(user, "vendor"):
            new_status = validated_data.get("cart_order_item_status")
            if new_status:
                if (
                    instance.is_canceled
                    or instance.cart_order_item_status == "delivered"
                ):
                    raise serializers.ValidationError(
                        "Cannot change status of delivered or canceled item."
                    )
                instance.cart_order_item_status = new_status
                validated_data.pop("cart_order_item_status")

        return super().update(instance, validated_data)


class ProductReviewSerializer(serializers.ModelSerializer):

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ProductReview
        fields = ["client", "product", "comment", "rating", "created_at", "updated_at"]
        read_only_fields = ["client", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user

        product = data.get("product")
        if not hasattr(user, "client"):
            raise serializers.ValidationError("only clients who can make comments")

        if ProductReview.objects.filter(client=user.client, product=product).exists():
            raise serializers.ValidationError("only one commend is possible")

        if not CartOrderItem.objects.filter(
            client=user.client, product=product
        ).exists():
            raise serializers.ValidationError(
                "you have not buy this product therefore you cannot make a comment on it !"
            )

        return data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        review_owner = instance.client

        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "only clients who can update or create feedbacks or reviews"
            )

        if user.client != review_owner:
            raise serializers.ValidationError(
                "you are not the owner of this comment , so you cannot modify it"
            )

        return super().update(instance, validated_data)


class WishlistSerializer(serializers.ModelSerializer):
    wid = serializers.ReadOnlyField()
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), many=True
    )

    class Meta:
        model = Wishlist
        fields = ["client", "wid", "products", "created_at"]
        read_only_fields = ["wid", "client", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("only clients that can have a wish list")

        try:
            Wishlist.objects.get(client=user.client)
            raise serializers.ValidationError("client has already a wish list")
        except Wishlist.DoesNotExist:
            pass
        return data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "only clients who can update or create a wishlist"
            )

        if instance.client != user.client:
            raise serializers.ValidationError("you are not the owner of this wishlist")

        return super().update(instance, validated_data)


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = ["user", "address", "status"]
        read_only_fields = ["user"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if instance.user != user:
            raise serializers.ValidationError("you are not the owner of this address")

        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    sid = serializers.ReadOnlyField()

    class Meta:
        model = ShoppingCart
        fields = ["sid", "client", "created_at", "updated_at"]
        read_only_fields = ["sid", "client", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        if ShoppingCart.objects.filter(client=user.client):
            raise serializers.ValidationError("this clint has already a shopping cart")

        return data


class CartItemSerializer(serializers.ModelSerializer):
    ciid = serializers.ReadOnlyField()
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartItem
        fields = [
            "ciid",
            "product",
            "quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["ciid", "shopping_cart", "created_at", "updated_at"]

    def validate(self, data):
        request = self.context["request"]
        user = request.user
        product = data["product"]
        quantity = data["quantity"]

        if quantity < 1:
            raise serializers.ValidationError(
                {"quantity": "Quantity must at least be 1"}
            )

        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "this user does not have a client account"
            )
        if not hasattr(user.client, "shopping_cart"):
            raise serializers.ValidationError("this user does not have a shopping cart")

        if not product.in_stock or product.quantity < quantity:
            raise serializers.ValidationError(
                {"quantity": "request quantity exceed available stock"}
            )

        shopping_cart = user.client.shopping_cart
        if CartItem.objects.filter(
            product=product, shopping_cart=shopping_cart
        ).exists():
            raise serializers.ValidationError(
                {"product": "This product already exist in your shopping cart"}
            )

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["shopping_cart"] = user.client.shopping_cart
        return CartItem.objects.create(**validated_data)


class GlobalOrderSerializer(serializers.ModelSerializer):
    gid = serializers.ReadOnlyField()

    class Meta:
        model = GlobalOrder
        fields = ["gid", "shopping_cart"]
        read_only_fields = ["gid", "shopping_cart"]

    def create(self, value):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account !")

        try:
            shopping_cart = ShoppingCart.objects.get(client=user.client)
        except ShoppingCart.DoesNotExist:
            raise serializers.ValidationError("this client has no shopping cart.")

        global_order = GlobalOrder.objects.create(shopping_cart=shopping_cart)
        return global_order


class SubCategorySerializer(serializers.ModelSerializer):
    scid = serializers.ReadOnlyField()

    class Meta:
        model = SubCategory
        fields = ["scid", "title", "description", "image", "created_at", "updated_at"]
