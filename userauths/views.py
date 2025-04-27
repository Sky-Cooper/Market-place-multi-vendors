from django.shortcuts import render
from .models import User, Vendor, Client, UserRoles, DeliveryAgent
from .serializers import (
    UserSerializer,
    VendorSerializer,
    ClientSerializer,
    DeliveryAgentSerializer,
)
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import RoleBasedQuerysetMixin, IsOwnerOrSuperAdmin


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    # TODO : make sure the second allow any to be is authenticated)

    def perform_create(self, serializer):
        if hasattr(self.request.user, "vendor"):
            raise PermissionDenied("user has already a vendor account profile")
        if hasattr(self.request.user, "client"):
            raise PermissionDenied(
                "the client can not have a vendor account in the same user account"
            )
        serializer.save()

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied(
                "you do not have the permission to access this object."
            )
        return obj


class DeliveryAgentViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAgent.objects.all()
    serializer_class = DeliveryAgentSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied("you are not the owner of this object")

        return obj


class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "client"):
            return Client.objects.get(user=user)
        if user.is_superuser:
            return Client.objects.all()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.AllowAny()]

    # TODO make sure to change the second allow any to is authenticated

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, "client"):
            raise PermissionDenied("user has already a client account profile")
        if hasattr(user, "vendor"):
            raise PermissionDenied(
                "a vendor can not have a client account in the same user account"
            )
        serializer.save()

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied(
                "you do not have the permission to access this object."
            )
        return obj
