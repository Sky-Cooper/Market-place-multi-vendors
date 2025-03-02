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
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(), allow_null=True
    )

    class Meta:
        model = CartOrder
        fields = [
            "oid",
            "vendor",
            "user",
            "total_payed",
            "paid_status",
            "order_date",
            "order_status",
            "payment_method",
        ]
        read_only_fields = [
            "vendor",
            "oid",
            "paid_status",
            "order_date",
            "order_status",
            "total_payed",
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


class CartOrderItemSerializer(serializers.ModelSerializer):
    coiid = serializers.ReadOnlyField()
    order = serializers.PrimaryKeyRelatedField(queryset=CartOrder.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartOrderItem
        fields = ["coiid", "order", "product", "quantity", "total_payed"]
        read_only_fields = ["total_payed", "coiid", "facture"]

        # the facture and the total_price should be calculated and generated, (make sure to send the facture in the gmail , for later imporvments not now)


class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ProductReview
        fields = ["user", "product", "comment", "rating"]

    def validate(self, data):
        user = self.context["request"].user

        product = data.get("product")
        if product:
            vendor = product.vendor
            vendor_user = vendor.user

            if vendor_user == user:
                raise serializers.ValidationError(
                    "you are the same vendor of this product , you cannot make self comments or reviews !!"
                )

            if ProductReview.objects.filter(
                client=user.client, product=product
            ).exists():
                raise serializers.ValidationError(
                    "you already made a comment on this product"
                )

            if not CartOrderItem.objects.filter(
                client=user.client, product=product
            ).exists():
                raise serializers.ValidationError(
                    "you have not buy this product therefore you cannot make a comment on it !"
                )

        return data


class WishlistSerializer(serializers.ModelSerializer):
    wid = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    products = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), many=True
    )

    class Meta:
        model = Wishlist
        fields = ["user", "wid", "products"]

    def validate_user(self, value):
        user = self.context["request"].user

        if Wishlist.objects.filter(user=user).exists():
            raise serializers.ValidationError("this user has already a wish list !!")

        return value


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = ["user", "address", "status"]


class ShoppingCartSerializer(serializers.ModelSerializer):
    sid = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ShoppingCart
        fields = ["sid", "client", "user"]

    def validate_user(self, value):
        user = self.context["request"].user

        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        if ShoppingCart.objects.filter(client=user.client).exists():
            raise serializers.ValidationError("this user has already a shopping cart")

        return value

    def create(self, validated_data):
        user = self.context["request"].user

        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        validated_data["client"] = user.client
        return super().create(validated_data)


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
        read_only_fields = ["total_price", "ciid", "shopping_cart"]

    def validate_stock(self, data):
        product = self.validated_data["product"]

        if not product.in_stock or product.quantity < 1:
            self.instance.delete()
            raise serializers.ValidationError("the product is out of stock")
        return data

    def create(self, validated_data):
        user = self.context["request"].user

        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        if not user.client.shopping_cart:
            raise serializers.ValidationError("this user has no shopping cart")

        if validated_data["quantity"] < 1:
            raise serializers.ValidationError("the quantity cannot be bellow 1")

        shopping_cart = ShoppingCart.objects.get(
            client=user.client
        )  # in my shopping_cart i have a field of client = ...(Client , on delete...,  related_name="shopping_cart")s

        validated_data["shopping_cart"] = shopping_cart
        cart_item = CartItem.objects.create(**validated_data)
        return cart_item


class GlobalOrderSerializer(serializers.ModelSerializer):
    gid = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GlobalOrder
        fields = ["gid", "shopping_cart", "user"]
        read_only_fields = ["gid", "user"]

    def validate_user(self, value):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account !")

        if not ShoppingCart.objects.filter(client=user.client).exists():
            raise serializers.ValidationError("this client has no shopping cart !!")

        return user

    def create(self, validated_data):
        user = self.context["request"].user
        shopping_cart = validated_data["shopping_cart"]
        cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)
        client = user.client

        vendors = {}

        for cart_item in cart_items:
            vendor = cart_item.product.vendor
            if vendor not in vendors:
                vendors[vendor] = []

            vendors[vendor].append(cart_item)

        global_order = GlobalOrder.objects.create(shopping_cart=shopping_cart)

        for vendor, cart_items in vendors.items():

            total_payed = sum(
                cart_item.product.price * cart_item.quantity for cart_item in cart_items
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
            print(f"Created CartOrder: {cart_order}")

            for cart_item in cart_items:
                cart_order_item = CartOrderItem.objects.create(
                    order=cart_order,
                    cart_item=cart_item,
                    quantity=cart_item.quantity,
                    total_payed=cart_item.product.price * cart_item.quantity,
                )

                print(f"Created CartOrderItem for CartOrder ID: {cart_order.id}")
                cart_order_item.save()

        return global_order


class SubCategorySerializer(serializers.ModelSerializer):
    scid = serializers.ReadOnlyField()

    class Meta:
        model = SubCategory
        fields = ["scid", "title", "description", "image", "created_at", "updated_at"]
