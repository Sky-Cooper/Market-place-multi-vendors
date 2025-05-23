from .models import User, Vendor, Client, UserRoles, DeliveryAgent
from rest_framework import serializers
import json
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from ecomapp.models import ProductReview, Product, FoodProduct
from django.db.models import Avg, Count
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        role = ""
        if user.is_superuser:
            role = "SUPER_USER"
        if hasattr(user, "vendor"):
            role = "VENDOR"

        if hasattr(user, "client"):
            role = "CLIENT"

        if hasattr(user, "delivery_agent"):
            role = "DELIVERY_AGENT"

        data["user_id"] = user.id
        data["email"] = user.email
        data["role"] = role
        return data


class UserSerializer(serializers.ModelSerializer):
    uid = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "uid",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "profile_image",
            "bio",
            "role",
            "gender",
        ]
        read_only_fields = ["role"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if "role" in validated_data and not request.user.is_superuser:
            raise PermissionError("only super users can update role")
        return super().update(instance, validated_data)


class VendorSerializer(serializers.ModelSerializer):
    vid = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    user = UserSerializer()
    total_sold = serializers.IntegerField(read_only=True)
    average_reviews = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            "vid",
            "user",
            "title",
            "description",
            "image",
            "country",
            "city",
            "image_url",
            "address",
            "total_sold",
            "average_reviews",
            "reviews_count",
        ]
        read_only_fields = ["vid", "image_url", "country"]

    def get_average_reviews(self, obj):
        logger.debug(f"Calculating average reviews for vendor: {obj.vid}")

        # Get the ContentTypes for Product and FoodProduct
        product_content_type = ContentType.objects.get_for_model(Product)
        food_product_content_type = ContentType.objects.get_for_model(FoodProduct)

        # Get related products and food products for the vendor
        vendor_products = Product.objects.filter(vendor=obj)
        food_products = FoodProduct.objects.filter(vendor=obj)

        # Filter reviews for both product and food product
        reviews_for_products = ProductReview.objects.filter(
            content_type=product_content_type,
            object_id__in=vendor_products.values_list("id", flat=True),
        )
        reviews_for_food_products = ProductReview.objects.filter(
            content_type=food_product_content_type,
            object_id__in=food_products.values_list("id", flat=True),
        )

        # Combine both querysets
        all_reviews = reviews_for_products | reviews_for_food_products

        if all_reviews.exists():
            average = all_reviews.aggregate(Avg("rating"))["rating__avg"]
            logger.debug(f"Average review for vendor {obj.vid}: {average}")
            return average or 0.0

        # No reviews found
        logger.debug(f"No reviews found for vendor: {obj.vid}")
        return 0.0

    def get_reviews_count(self, obj):
        logger.debug(f"Calculating reviews count for vendor: {obj.vid}")

        # Get the ContentTypes for Product and FoodProduct
        product_content_type = ContentType.objects.get_for_model(Product)
        food_product_content_type = ContentType.objects.get_for_model(FoodProduct)

        # Get related products and food products for the vendor
        vendor_products = Product.objects.filter(vendor=obj)
        food_products = FoodProduct.objects.filter(vendor=obj)

        # Filter reviews for both product and food product
        reviews_for_products = ProductReview.objects.filter(
            content_type=product_content_type,
            object_id__in=vendor_products.values_list("id", flat=True),
        )
        reviews_for_food_products = ProductReview.objects.filter(
            content_type=food_product_content_type,
            object_id__in=food_products.values_list("id", flat=True),
        )

        # Combine both querysets
        all_reviews = reviews_for_products | reviews_for_food_products

        count = all_reviews.count()
        logger.debug(f"Review count for vendor {obj.vid}: {count}")
        return count

    def validate(self, data):
        user = self.context["request"].user
        if (
            hasattr(user, "client")
            or hasattr(user, "vendor")
            or user.is_superuser
            or hasattr(user, "delivery_agent")
        ):
            raise serializers.ValidationError("this user is already linked")

        if "total_sold" in data:
            raise serializers.ValidationError("you cannot update the total sold")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop("user", None)
        print("DEBUG: user_data type =>", type(user_data))  # <--- Add this line

        if not user_data:
            raise serializers.ValidationError("User information is required.")

        if not isinstance(user_data, dict):
            raise serializers.ValidationError("User data must be a dictionary.")

        password = user_data.pop("password", None)
        if not password:
            raise serializers.ValidationError("Password is required.")

        user = User(**user_data)
        user.set_password(password)
        user.role = UserRoles.VENDOR
        user.save()

        vendor = Vendor.objects.create(user=user, **validated_data)
        return vendor

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    # def to_internal_value(self, data):
    #     data = data.copy()
    #     user_data = data.get("user")

    #     if isinstance(user_data, str):
    #         print(user_data)
    #         try:
    #             data["user"] = json.loads(user_data)
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError(
    #                 {"user": "User field must be a valid JSON string."}
    #             )

    #     return super().to_internal_value(data)


class ClientSerializer(serializers.ModelSerializer):
    cid = serializers.ReadOnlyField()
    user = UserSerializer()

    class Meta:
        model = Client

        fields = ["cid", "user", "list_of_interest", "is_active", "is_banned"]
        read_only_fields = ["cid", "is_active", "is_banned"]

    def validate(self, data):
        user = self.context["request"].user
        if (
            hasattr(user, "client")
            or hasattr(user, "vendor")
            or user.is_superuser
            or hasattr(user, "delivery_agent")
        ):
            raise serializers.ValidationError("this user is already linked")
        return data

    def validate_list_of_interest(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "Invalid JSON format for list_of_interest."
                )
        if not isinstance(value, list):
            raise serializers.ValidationError("list_of_interest must be a list.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user_role = UserRoles.CLIENT
        password = user_data.pop("password")
        user = User(**user_data)
        user.set_password(password)
        user.role = user_role
        user.save()
        client = Client.objects.create(user=user, **validated_data)
        return client


class DeliveryAgentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryAgent
        fields = [
            "id",
            "user",
            "city",
            "country",
            "identity_picture",
            "profile_picture",
            "is_active",
            "is_banned",
            "ban_expired_at",
            "created_at",
            "updated_at",
            "profile_picture_url",
        ]
        read_only_fields = [
            "id",
            "country",
            "is_active",
            "is_banned",
            "ban_expired_at",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        user = self.context["request"].user
        data = super().to_representation(instance)
        if hasattr(user, "client") or hasattr(user, "vendor"):
            data.pop("identity_picture", None)
            data.pop("is_banned", None)

        if data.get("user", {}).get("role", None) not in [
            role.value for role in UserRoles
        ]:
            raise serializers.ValidationError("this user has no role")
        return data

    def validate(self, data):
        user = self.context["request"].user
        if (
            hasattr(user, "client")
            or hasattr(user, "vendor")
            or user.is_superuser
            or hasattr(user, "delivery_agent")
        ):
            raise serializers.ValidationError("this user is already linked")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user_role = UserRoles.DELIVERY_AGENT
        password = user_data.pop("password")
        user = User(**user_data)
        user.set_password(password)
        user.role = user_role
        user.save()
        delivery_agent = DeliveryAgent.objects.create(user=user, **validated_data)
        return delivery_agent

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user != instance.user and not user.is_superuser:
            raise serializers.ValidationError(
                "you are not the owner of this delivery agent instance"
            )

        if not user.is_superuser and not hasattr(user, "delivery_agent"):
            raise serializers.ValidationError(
                "only delivery agents or super users who can access this"
            )

        delivery_agent_forbidden_fields = [
            "is_active",
            "is_banned",
            "ban_expired_at",
            "created_at",
            "updated_at",
        ]
        for field in delivery_agent_forbidden_fields:
            if field in validated_data:
                raise serializers.ValidationError(
                    f"you cannot modify or update this field {field}"
                )

        user_data = validated_data.pop("user", {})
        user_forbidden_fields = ["uid", "role", "is_active", "created_at", "updated_at"]
        for field in user_forbidden_fields:
            if field in user_data:
                raise serializers.ValidationError(
                    f"you cannot modify or update this field {field}"
                )

        return super().update(instance, validated_data)

    def get_profile_picture_url(self, obj):
        request = self.context["request"]
        if obj.profile_picture is not None:
            return request.build_absolute_uri(obj.profile_picture)
