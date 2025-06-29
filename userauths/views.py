from django.shortcuts import render
from .models import User, Vendor, Client, UserRoles, DeliveryAgent
from .serializers import (
    UserSerializer,
    VendorSerializer,
    ClientSerializer,
    DeliveryAgentSerializer,
    CustomTokenObtainPairSerializer,
)
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import RoleBasedQuerysetMixin, IsOwnerOrSuperAdmin
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.response import Response
from .filters import VendorFilter, VendorPagination
from django.db.models import Q, Sum, Count
from rest_framework import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = PageNumberPagination

    @action(
        detail=False,
        methods=["get"],
        url_path="top-sellers",
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def top_sellers(self, request):
        top_sellers_data = Vendor.objects.all().order_by("-total_sold")[:6]

        serializer = self.get_serializer(
            top_sellers_data, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create", "top_sellers"]:
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


class VendorListAPIView(generics.ListAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    pagination_class = VendorPagination
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter,
    ]
    filterset_class = VendorFilter
    search_fields = ["city", "total_sold"]
    ordering_fields = ["total_sold"]
    ordering = ["-total_sold"]


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
            return Client.objects.filter(user=user)
        if user.is_superuser:
            return Client.objects.all()
        return Client.objects.none()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.AllowAny()]

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
