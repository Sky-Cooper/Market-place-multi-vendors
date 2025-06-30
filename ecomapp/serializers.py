from rest_framework import serializers
from .models import *
from django.utils.html import mark_safe
from userauths.models import *
from taggit.serializers import TaggitSerializer, TagListSerializerField
from .helpers import is_valid_client_and_order
from userauths.serializers import VendorSerializer, UserSerializer, ClientSerializer
from django.db.models import Avg


class SectorSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Sector
        fields = [
            "id",
            "title",
            "description",
            "image",
            "image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "image_url", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can access this resource"
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can access this resource"
            )

        return super().update(instance, validated_data)

    def get_image_url(self, obj):
        request = self.context["request"]
        return request.build_absolute_uri(obj.image) if obj.image else None


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    sector = serializers.PrimaryKeyRelatedField(queryset=Sector.objects.all())

    class Meta:
        model = Category
        fields = ["id", "sector", "title", "description", "image", "image_url"]
        read_only_fields = ["id", "image_url"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["sector"] = SectorSerializer(instance.sector, context=self.context).data
        return rep

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can access this resource"
            )
        return super().create(validated_data)

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


class SubCategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "title",
            "category",
            "description",
            "image",
            "image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "image_url"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["category"] = CategorySerializer(
            instance.category, context=self.context
        ).data
        return rep

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "this resource is only accessed by super user"
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not user.super_user:
            raise serializers.ValidationError(
                "this resource is only accessed by super admin"
            )

        return super().update(instance, validated_data)

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


class ProductImagesSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImages
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "only vendors that are allowed to access this resource"
            )

        if hasattr(user, "vendor"):
            product = data.get("product")
            if product.vendor != user.vendor:
                raise serializers.ValidationError(
                    "you are not the owner of this product"
                )

        return data


class FoodProductImagesSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FoodProductImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "only vendors that are allowed to access this resource"
            )

        if hasattr(user, "vendor"):
            product = data.get("product")
            if product.vendor != user.vendor:
                raise serializers.ValidationError(
                    "you are not the owner of this product"
                )

        return data


class ProductColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductColor
        fields = ["color"]


class ProductReviewSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        slug_field="model",
        queryset=ContentType.objects.filter(model__in=["product", "foodproduct"]),
    )
    client = ClientSerializer(read_only=True)
    object_id = serializers.IntegerField()

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "client",
            "content_type",
            "object_id",
            "comment",
            "rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "client", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("Only clients can review.")

        model_class = data["content_type"].model_class()
        try:
            item = model_class.objects.get(id=data["object_id"])
        except model_class.DoesNotExist:
            raise serializers.ValidationError("Item does not exist.")

        if ProductReview.objects.filter(
            client=user.client,
            content_type=data["content_type"],
            object_id=data["object_id"],
        ).exists():
            raise serializers.ValidationError("You already reviewed this item.")

        if not CartOrderItem.objects.filter(
            client=user.client,
            content_type=data["content_type"],
            object_id=data["object_id"],
        ).exists():
            raise serializers.ValidationError("You must purchase before reviewing.")

        return data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user.client != instance.client:
            raise serializers.ValidationError("You do not own this review.")
        return super().update(instance, validated_data)


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "product", "size", "quantity"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "vendor") and not user.is_superuser:
            raise serializers.ValidationError(
                "only vendors and super users that can access this resource"
            )
        if hasattr(user, "vendor"):

            product = validated_data.get("product")
            if product.vendor != user.vendor:
                raise serializers.ValidationError(
                    "you are not the owner of the product"
                )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "vendor") and not user.is_superuser:
            raise serializers.ValidationError(
                "only vendors and super users that can access this resource"
            )

        if hasattr(user, "vendor"):
            if instance.product.vendor != user.vendor:
                raise serializers.ValidationError(
                    "you are not the owner of this product size object, you cannot modify it"
                )

        return super().update(instance, validated_data)


class ProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)
    colors = serializers.ListField(
        child=serializers.ChoiceField(choices=ColorChoices.choices),
        required=False,
        write_only=True,
    )
    color_list = serializers.SerializerMethodField(read_only=True)
    images = ProductImagesSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    image_url = serializers.SerializerMethodField()
    tags = TagListSerializerField()
    vendor = VendorSerializer(read_only=True)
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all()
    )
    average_reviews = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    sector = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "sub_category",
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
            "details",
            "potential_guarantee_period",
            "colors",
            "color_list",
            "images",
            "uploaded_images",
            "vendor",
            "created_at",
            "updated_at",
            "reviews",
            "average_reviews",
            "total_reviews",
            "long_description",
            "sizes",
            "sector",
        ]
        read_only_fields = [
            "id",
            "discount_percentage",
            "details",
            "color_list",
            "images",
            "image_url",
            "reviews",
            "created_at",
            "updated_at",
            "sizes",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["sub_category"] = SubCategorySerializer(
            instance.sub_category, context=self.context
        ).data
        return rep

    def get_sector(self, obj):
        sector = obj.sub_category.category.sector.title
        if sector:
            return sector

    def get_average_reviews(self, obj):
        average_rating = obj.reviews.all().aggregate(Avg("rating"))["rating__avg"]
        return round(average_rating or 0.0)

    def get_total_reviews(self, obj):
        return obj.reviews.all().count()

    def get_color_list(self, obj):
        return list(obj.colors.values_list("color", flat=True))

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate_vendor(self, value):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "You cannot create a product because this current user has no vendor account"
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "This current logged in user has no vendor"
            )

        if user.vendor.is_banned:
            raise serializers.ValidationError("This vendor is banned")

        validated_data["vendor"] = user.vendor
        tags = validated_data.pop("tags", [])

        colors = validated_data.pop("colors", [])

        uploaded_images = validated_data.pop("uploaded_images", [])
        product = Product.objects.create(**validated_data)
        product.tags.add(*tags)

        for color in colors:
            ProductColor.objects.create(product=product, color=color)

        for image in uploaded_images:
            ProductImages.objects.create(product=product, image=image)

        return product

    def get_tags(self, obj):
        return list(obj.tags.names())


class FoodProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    reviews = ProductReviewSerializer(many=True, read_only=True)
    images = FoodProductImagesSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    image_url = serializers.SerializerMethodField()
    tags = TagListSerializerField()
    vendor = VendorSerializer(read_only=True)
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all()
    )
    average_reviews = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    sector = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FoodProduct
        fields = [
            "id",
            "title",
            "description",
            "sub_category",
            "old_price",
            "price",
            "tags",
            "image",
            "image_url",
            "specifications",
            "is_active",
            "in_stock",
            "discount_percentage",
            "quantity",
            "details",
            "images",
            "uploaded_images",
            "vendor",
            "created_at",
            "updated_at",
            "ingredients",
            "expired_at",
            "weight_in_grams",
            "calories",
            "is_vegan",
            "reviews",
            "average_reviews",
            "total_reviews",
            "sector",
        ]

        read_only_fields = [
            "id",
            "image_url",
            "discount_percentage",
            "details",
            "images",
            "created_at",
            "updated_at",
            "expired_at",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["sub_category"] = SubCategorySerializer(
            instance.sub_category, context=self.context
        ).data
        return rep

    def get_sector(self, obj):
        sector = obj.sub_category.category.sector.title
        if sector:
            return sector

    def get_average_reviews(self, obj):
        average_reviews = obj.reviews.all().aggregate(Avg("rating"))["rating__avg"]
        return round(average_reviews or 0.0)

    def get_total_reviews(self, obj):
        return obj.reviews.all().count()

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "this current logged in user  has no vendor"
            )

        if user.vendor.is_banned:
            raise serializers.ValidationError("this vendor is banned")

        validated_data["vendor"] = user.vendor
        tags = validated_data.pop("tags", [])
        uploaded_images = validated_data.pop("uploaded_images", [])
        food_product = FoodProduct.objects.create(**validated_data)
        food_product.tags.add(*tags)
        for image in uploaded_images:
            FoodProductImage.objects.create(food_product=food_product, image=image)

        return food_product

    def get_tags(self, obj):
        return list(obj.tags.name())


class CartOrderSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = CartOrder
        fields = [
            "id",
            "vendor",
            "total_payed",
            "order_date",
            "payment_method",
            "global_order",
            "is_canceled",
            "order_status",
            "delivery_option",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "order_date",
            "total_payed",
            "payment_method",
            "is_active",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can create an order"
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if (
            not hasattr(user, "client")
            and not hasattr(user, "vendor")
            and not user.is_superuser
        ):
            raise serializers.ValidationError(
                "only super users, clients , vendors who can update a cart order"
            )

        if instance.is_canceled:
            raise serializers.ValidationError("you cannot update a canceled order")
        if instance.order_status == "delivered":
            raise serializers.ValidationError("you cannot update a delivered order")

        if instance.claimed_orders.filter(is_failed=False).exists():
            raise serializers.ValidationError("you cannot update a claimed order")

        if instance.order_status == "canceled":
            raise serializers.ValidationError("you cannot update a canceled order")

        if hasattr(user, "client"):
            if user.client != instance.client:
                raise serializers.ValidationError(
                    "you are not the owner of this particular cart order"
                )
            allowed_fields = {"delivery_option", "is_canceled"}
            if not set(validated_data.keys()).issubset(allowed_fields):
                raise serializers.ValidationError(
                    "as a client you are only allowed to update delivery option or is_canceled"
                )

        if hasattr(user, "vendor"):
            allowed_fields = {"order_status"}
            if not set(validated_data.keys()).issubset(allowed_fields):
                raise serializers.ValidationError(
                    {
                        "error": "as a vendor you are only allowed to update the order status"
                    }
                )
            if instance.order_status == "confirmed":
                raise serializers.ValidationError("you cannot update a confirmed order")

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


class CartItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    food_product = FoodProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "food_product",
            "quantity",
            "created_at",
            "updated_at",
            "total_price",
            "is_ordered",
            "size",
        ]
        read_only_fields = fields


class CartOrderItemSerializer(serializers.ModelSerializer):
    cart_item = CartItemReadSerializer(read_only=True)
    cart_order_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartOrderItem
        fields = [
            "id",
            "order",
            "cart_item",
            "created_at",
            "updated_at",
            "total_payed",
            "is_canceled",
            "is_canceled_by_vendor",
            "is_active",
            "cart_order_status",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "potential_delivery_days",
            "total_payed",
            "is_active",
        ]

    def get_cart_order_status(self, obj):
        return obj.order.order_status

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can create a cart order item"
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if (
            not hasattr(user, "client")
            and not user.is_superuser
            and not hasattr(user, "vendor")
        ):
            raise serializers.ValidationError(
                "only client or super user or vendors who can update a cart order item"
            )

        if (
            instance.is_canceled
            or instance.is_canceled_by_vendor
            or not instance.is_active
        ):
            raise serializers.ValidationError(
                "you cannot update a canceled or inactive cart item order"
            )

        if hasattr(user, "client"):
            allowed_fields = {"is_canceled"}

            if not set(validated_data.keys()).issubset(allowed_fields):
                raise serializers.ValidationError(
                    "clients can only update the cancellation attribute"
                )

            if "is_canceled" in validated_data:
                if instance.is_canceled or instance.order.order_status == "delivered":
                    raise serializers.ValidationError(
                        "Cannot cancel  an already delivered or canceled item."
                    )
                instance.is_canceled = True
                validated_data.pop("is_canceled")

        if hasattr(user, "vendor"):
            user_vendor = user.vendor
            allowed_fields = {"is_canceled_by_vendor"}
            obj_vendor = instance.order.vendor
            if user_vendor != obj_vendor:
                raise serializers.ValidationError(
                    "you are not the owner of this cart order item"
                )
            if "is_canceled_by_vendor" in validated_data:
                if instance.is_canceled or instance.order.order_status == "delivered":
                    raise serializers.ValidationError(
                        "Cannot change status of delivered or canceled item."
                    )
                instance.is_canceled_by_vendor = validated_data.pop(
                    "is_canceled_by_vendor"
                )

        if not set(validated_data.keys()).issubset(allowed_fields):
            raise serializers.ValidationError(
                "you are not allowed to update these fields"
            )
        instance.save()
        return instance


class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    food_products = FoodProductSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "client", "products", "food_products", "created_at"]
        read_only_fields = ["id", "client", "created_at"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client") or instance.client != user.client:
            raise serializers.ValidationError("you are not the owner of this wishlist")

        return super().update(instance, validated_data)


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = ["id", "user", "address", "status"]
        read_only_fields = ["id", "user"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if instance.user != user:
            raise serializers.ValidationError("you are not the owner of this address")

        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ["id", "client", "created_at", "updated_at"]
        read_only_fields = ["id", "client", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("this user has no client account")

        if ShoppingCart.objects.filter(client=user.client):
            raise serializers.ValidationError("this client has already a shopping cart")

        return data


class CartItemWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False
    )
    food_product = serializers.PrimaryKeyRelatedField(
        queryset=FoodProduct.objects.all(), required=False
    )

    class Meta:
        model = CartItem
        fields = [
            "product",
            "food_product",
            "quantity",
            "size",
        ]

    def create(self, validated_data):
        user = self.context["request"].user

        if not hasattr(user, "client") or user.is_superuser:
            raise serializers.ValidationError(
                {"error": "Only clients (not superusers) can create cart items."}
            )

        product = validated_data.get("product")
        food_product = validated_data.get("food_product")
        quantity = validated_data.get("quantity")

        if (not product and not food_product) or (product and food_product):
            raise serializers.ValidationError(
                "You must provide either a product or a food product, but not both."
            )

        if quantity is not None and quantity < 1:
            raise serializers.ValidationError("The quantity must be at least 1.")

        client = user.client
        shopping_cart = getattr(client, "shopping_cart", None)

        if not shopping_cart:
            raise serializers.ValidationError("This client has no shopping cart.")

        product = validated_data.get("product")
        food_product = validated_data.get("food_product")
        quantity = validated_data.get("quantity", 1)

        if product:
            if not product.in_stock or product.quantity < quantity:
                raise serializers.ValidationError(
                    {"quantity": "Requested quantity exceeds product stock."}
                )
            if shopping_cart.cart_items.filter(
                product=product, is_ordered=False
            ).exists():
                raise serializers.ValidationError(
                    {"product": "This product is already in your cart and not ordered."}
                )

        if food_product:
            if not food_product.in_stock or (
                food_product.quantity and food_product.quantity < quantity
            ):
                raise serializers.ValidationError(
                    {"quantity": "Requested quantity exceeds food product stock."}
                )
            if shopping_cart.cart_items.filter(
                food_product=food_product, is_ordered=False
            ).exists():
                raise serializers.ValidationError(
                    {
                        "food_product": "This food product is already in your cart and not ordered."
                    }
                )

        validated_data["shopping_cart"] = shopping_cart
        return CartItem.objects.create(**validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if not hasattr(user, "client"):
            raise serializers.ValidationError("This user has no client account.")

        if instance.is_ordered:
            raise serializers.ValidationError("You cannot modify an ordered cart item.")

        quantity = validated_data.get("quantity")
        if quantity is None or quantity < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")

        if instance.product:
            if not instance.product.in_stock or instance.product.quantity < quantity:
                raise serializers.ValidationError(
                    {"product": "Product is out of stock or insufficient quantity."}
                )
        elif instance.food_product:
            if not instance.food_product.in_stock or (
                instance.food_product.quantity
                and instance.food_product.quantity < quantity
            ):
                raise serializers.ValidationError(
                    {
                        "food_product": "Food product is out of stock or insufficient quantity."
                    }
                )

        return super().update(instance, validated_data)


class GlobalOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = GlobalOrder
        fields = [
            "id",
            "shopping_cart",
            "total_price",
            "payment_method",
            "address",
            "city",
            "country",
            "created_at",
            "updated_at",
            "delivery_option",
        ]
        read_only_fields = [
            "id",
            "shopping_cart",
            "total_price",
            "payment_method",
            "created_at",
            "updated_at",
            "country",
        ]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError("only clients who can buy")
        client = user.client
        if not hasattr(client, "shopping_cart"):
            raise serializers.ValidationError("this client has no shopping cart")

        return data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can update this object"
            )

        return super().update(instance, validated_data)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["id", "price", "title", "description" "max_products", "support_level"]

        read_only_fields = ["id"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only superusers who can access this resource"
            )

        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "vendor",
            "created_at",
            "updated_at",
            "subscription_plan",
            "expired_at",
            "total_payed",
            "is_canceled",
        ]

        read_only_fields = [
            "id",
            "vendor",
            "created_at",
            "updated_at",
            "expired_at",
            "total_payed",
        ]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "vendor") and not user.is_superuser:
            raise serializers.ValidationError(
                "this resource is only accessed by vendors"
            )
        return data


class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionFeature
        fields = ["id", "title", "description", "subscription_plan"]
        read_only_fields = ["id"]

        def validate(self, data):
            user = self.context["request"].user
            if not user.is_superuser:
                raise serializers.ValidationError(
                    "this resource is only accessed by superusers"
                )

            return data


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = ["id", "created_at", "updated_at", "amount_payed", "subscription"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "only vendors who can access this resource"
            )
        subscription = data.get("subscription")
        if subscription:
            if not subscription.is_expired:
                raise serializers.ValidationError(
                    "you still have an active subscription"
                )

            if subscription.vendor != user.vendor:
                raise serializers.ValidationError("you dont own this subscription")

        return data

    def create(self, validated_data):
        subscription = validated_data.get("subscription")
        payment = SubscriptionPayment.objects.create(**validated_data)

        if subscription:
            subscription.expired_at = payment.created_at + timedelta(days=30)
            subscription.save()

        return payment


class DeliveryRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRating
        fields = ["id", "claimed_order", "rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        claimed_order = data.get("claimed_order")
        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "only clients who can make a delivery rating object"
            )
        if not claimed_order:
            raise serializers.ValidationError(
                {"claimed_order": "this field is required"}
            )

        if user.client != claimed_order.order.client:
            raise serializers.ValidationError(
                {"claimed_order": "you are not the owner of this order"}
            )

        if claimed_order.order.delivery_status != "delivered":
            raise serializers.ValidationError(
                {"claimed_order": "This order has not been delivered yet."}
            )

        return data

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client"):
            raise serializers.ValidationError(
                "only clients who can make delivery ratings"
            )

        claimed_order = validated_data.get("claimed_order", None)
        if claimed_order is None:
            raise serializers.ValidationError("there is no related claimed order")

        client_based_on_claimed_order = claimed_order.order.client
        if user.client != client_based_on_claimed_order:
            raise serializers.ValidationError(
                "you are not the owner of this particular order , therefore you cannot make a delivery rating on it"
            )

        order_based_on_claimed_order = claimed_order.order
        if not order_based_on_claimed_order.delivery_status == "delivered":
            raise serializers.ValidationError(
                "the order is not yet delivered , therefore you cannot make a rating comment on the delivery agent"
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "client") or user.is_superuser:
            raise serializers.ValidationError(
                "only clients or super users who are allowed to make updates on delivery ratings"
            )

        if hasattr(user, "client"):
            if user.client != instance.client:
                raise serializers.ValidationError(
                    "you are not the owner of this particular object in order to delete it"
                )
            allowed_fields = {"rating", "comment"}

            if not set(validated_data.keys()).issubset(allowed_fields):
                raise serializers.ValidationError(
                    "as a client you can only update rating and comment attribute regarding the delivery rating model"
                )

        return super().update(instance, validated_data)


class ClaimOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimedOrder
        fields = [
            "id",
            "created_at",
            "updated_at",
            "order",
            "is_confirmed_by_vendor",
            "expiration_date_time",
            "is_failed",
            "delivery_status",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "expiration_time_out",
            "is_failed",
        ]

    def validate(self, data):
        user = self.context["request"].user
        if (
            not hasattr(user, "delivery_agent")
            and not hasattr(user, "vendor")
            and not user.is_superuser
        ):
            raise serializers.ValidationError(
                "only delivery agents , vendors , super users that can access this resource"
            )
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        if not hasattr(user, "delivery_agent") and not user.is_superuser:
            raise serializers.ValidationError(
                "only delivery agents and super users who can access this resource"
            )
        order = validated_data.get("order", None)
        if (
            order.is_canceled
            or not order.order_status == "confirmed"
            or not order.is_active
        ):
            raise serializers.ValidationError(
                "you cannot claim a canceled or delivered or not confirmed order"
            )

        if not order.delivery_option:
            raise serializers.ValidationError("the order is not asking for a delivery")
        if (
            order.claimed_orders.filter(is_failed=False)
            .exclude(delivery_status="delivered")
            .exists()
        ):
            raise serializers.ValidationError(
                "this order is already claimed and the expiration time is not done yet"
            )

        if hasattr(user, "delivery_agent"):

            if ClaimedOrder.objects.filter(
                delivery_agent=user.delivery_agent, is_active=True
            ).exists():
                raise serializers.ValidationError(
                    "you have already claimed an order , you have to deliver it before claiming the next one"
                )

            if ClaimedOrder.objects.filter(
                order=order, delivery_agent=user.delivery_agent, is_failed=True
            ).exists():
                raise serializers.ValidationError(
                    "you already failed to claim this order , you cannot have a second attempt"
                )
            print(f"delivery agent city  {user.delivery_agent.city}")
            print(f"vendor city {order.vendor.city}")
            if user.delivery_agent.city != order.vendor.city:
                raise serializers.ValidationError(
                    "you cannot claim this order because it does not belongs to the city that you living in"
                )

        validated_data["delivery_agent"] = user.delivery_agent

        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if (
            not hasattr(user, "delivery_agent")
            and not hasattr(user, "vendor")
            and not user.is_superuser
        ):
            raise serializers.ValidationError(
                "only delivery agents , vendors , super users who can access this resource"
            )

        if instance.is_failed:
            raise serializers.ValidationError(
                "you cannot update a failed claimed order"
            )

        if hasattr(instance, "cancellation_request"):
            raise serializers.ValidationError(
                "you cannot update a claimed order that has a cancellation request"
            )

        if instance.delivery_status == "delivered":
            raise serializers.ValidationError(
                "you cannot update a claimed order that has been delivered"
            )

        if instance.order.order_status == "delivered":
            raise serializers.ValidationError("you cannot update a delivered order")

        if hasattr(user, "delivery_agent"):
            allowed_fields = {"delivery_status"}
            invalid_fields = set(validated_data.keys()).issubset(allowed_fields)
            if not invalid_fields:
                raise serializers.ValidationError(
                    "you provided more than the allowed arguments as a delivery agent"
                )
            delivery_status = validated_data.get("delivery_status", None)
            if delivery_status is not None:
                if (
                    delivery_status == "delivered"
                    and not instance.order.order_status == "delivered"
                    and instance.is_confirmed_by_vendor
                ):
                    instance.order.order_status = "delivered"
                    instance.order.save(update_fields=["order_status"])

        if hasattr(user, "vendor"):
            order_vendor = instance.order.vendor
            if order_vendor != user.vendor:
                raise serializers.ValidationError("you are not the order's vendor")
            allowed_fields = {"is_confirmed_by_vendor"}
            invalid_fields = set(validated_data.keys()).issubset(allowed_fields)
            print(validated_data)
            if not invalid_fields:
                raise serializers.ValidationError(
                    "you provided more than the allowed arguments as a vendor"
                )

        return super().update(instance, validated_data)


class DeliveryAgentStrikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAgentStrike
        fields = [
            "id",
            "delivery_agent",
            "reason",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_active"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError("only superusers who can create a strike")
        return data


class ClientStrikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientStrike
        fields = ["id", "client", "reason", "created_at", "updated_at", "is_active"]
        read_only_fields = ["id", "created_at", "updated_at", "is_active"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can create a client strike"
            )

        return data


class VendorStrikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorStrike
        fields = ["id", "vendor", "reason", "created_at", "updated_at", "is_active"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError("only super users who can create strikes")

        return data


class NotificationSerializer(serializers.ModelSerializer):
    target_type = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()
    target_str = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "message",
            "content_type",
            "object_id",
            "notification_type",
            "created_at",
            "updated_at",
            "target_type",
            "target_id",
            "target_str",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "target_type",
            "target_id",
            "target_str",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            raise serializers.ValidationError(
                "only super users who can create notification"
            )

        return validated_data

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if not user.is_superuser:
            allowed_fields = {"is_read"}

            if not set(validated_data.keys()).issubset(allowed_fields):
                raise serializers.ValidationError(
                    "you provided more than the allowed fields"
                )

        return super().update(instance, validated_data)

    def get_target_type(self, obj):
        return obj.content_type.model

    def get_target_id(self, obj):
        return obj.object_id

    def get_target_str(self, obj):
        return str(obj.target)


class TestimonialSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Testimonial
        fields = ["id", "user", "message", "rating", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if (
            not hasattr(user, "vendor")
            and not hasattr(user, "client")
            and not hasattr(user, "delivery_agent")
        ):
            raise serializers.ValidationError(
                "only vendors, clients , delivery agents  that can create a testimonial"
            )
        if Testimonial.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "sorry! you have already declared you testimony"
            )
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return Testimonial.objects.create(user=user, **validated_data)


from rest_framework import serializers
from .models import Product, FoodProduct
from .serializers import ProductSerializer, FoodProductSerializer


class AiMessageSerializer(serializers.Serializer):
    message = serializers.CharField()

    class Meta:
        fields = ["message"]


class TopProductSerializer(serializers.Serializer):
    total_quantity_sold = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Product
        fields = [
            "id",
            "price",
            "title",
            "image",
            "quantity",
            "total_quantity_sold",
            "total_orders",
            "total_earned",
        ]


class SalesOverTimeSerializer(serializers.Serializer):

    class Meta:
        model = CartOrder
        fields = ["id", "order_date", "total_payed"]


class TopFoodProductsSerializer(serializers.Serializer):
    total_quantity_sold = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_earned = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = FoodProduct
        fields = [
            "id",
            "price",
            "title",
            "image",
            "total_quantity_sold",
            "total_earned",
            "total_orders",
        ]
