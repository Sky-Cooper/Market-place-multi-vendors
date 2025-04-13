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

    def validate(self, data):
        user = self.context["request"].user
        if hasattr(user, "client") or hasattr(user, "vendor") or user.is_superuser:
            raise serializers.ValidationError("this user is already linked")
        return data

    def create(self, validated_data):
        if validated_data:
            user_data = validated_data.pop("user")
            password = user_data.pop("password")
            user = User(**user_data)
            user.set_password(password)
            user.save()
            try:
                vendor = Vendor.objects.create(user=user, **validated_data)

            except Exception as e:
                user.delete()
                raise serializers.ValidationError(f"exception : {e}")

            return vendor

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if obj.image else None


class ClientSerializer(serializers.ModelSerializer):
    cid = serializers.ReadOnlyField()
    user = UserSerializer()

    class Meta:
        model = Client

        fields = ["cid", "user", "list_of_interest", "is_active", "is_banned"]
        read_only_fields = ["cid", "is_active", "is_banned"]

    def validate(self, data):
        user = self.context["request"].user
        if hasattr(user, "client") or hasattr(user, "vendor") or user.is_superuser:
            raise serializers.ValidationError("this user is already linked")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = user_data.pop("password")
        user = User(**user_data)
        user.set_password(password)
        user.save()
        client = Client.objects.create(user=user, **validated_data)
        return client
