from rest_framework import permissions
from .models import UserRoles


class IsOwnerOrSuperAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user or request.user.role == UserRoles.SUPER_ADMIN


class RoleBasedQuerysetMixin:

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRoles.SUPER_ADMIN:
            return self.queryset
        return self.queryset.filter(user=user)


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsVendorOrClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, "vendor") or hasattr(request.user, "client")
