from django.shortcuts import render
from .models import User, Vendor, Client, UserRoles
from .serializers import UserSerializer, VendorSerializer, ClientSerializer
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


class VendorViewSet(RoleBasedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        if hasattr(self.request.user, "vendor"):
            raise PermissionDenied("user has already a vendor account profile")
        serializer.save(user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied(
                "you do not have the permission to access this object."
            )
        return obj


class ClientViewSet(RoleBasedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperAdmin]

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, "client"):
            raise PermissionDenied("user has already a client account profile")
        serializer.save(user=user)

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRoles.SUPER_ADMIN:
            return Client.objects.all()
        if hasattr(user, "client"):
            return Client.objects.get(user=user)
        return Client.objects.none

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied(
                "you do not have the permission to access this object."
            )
        return obj
