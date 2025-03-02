from .models import User, Vendor, Client
from rest_framework import serializers


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
            "bio",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create_user(password=password, **validated_data)
        return user


class VendorSerializer(serializers.ModelSerializer):
    vid = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Vendor
        fields = [
            "vid",
            "user",
            "title",
            "description",
            "image",
            "image_url",
            "address",
            "contact",
            "shipping_time",
            "guarantee_period",
        ]
        read_only_fields = ["chat_response_time", "average rating", "vid"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def validate_user(self, value):
        user = self.context["request"].user

        if hasattr(user, "vendor"):
            raise serializers.ValidationError(
                "you have already created a vendor profile"
            )

        return value


class ClientSerializer(serializers.ModelSerializer):
    cid = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Client

        fields = ["cid", "user", "list_of_interest", "is_active", "is_banned"]
        read_only_fields = ["cid", "is_active", "is_banned"]

    def validate_user(self, value):
        user = self.context["request"].user

        if hasattr(user, "client"):
            raise serializers.ValidationError(
                "you have already created a client profile"
            )

        return value
