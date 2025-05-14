from django.contrib import admin
from userauths.models import User, Vendor, Client, DeliveryAgent
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "profile_image",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "bio",
                    "role",
                    "profile_image",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if change:
            existing_user = User.objects.get(pk=obj.pk)
            if existing_user.password != obj.password:
                obj.set_password(obj.password)
        else:
            obj.set_password(obj.password)
        obj.save()


class VendorAdmin(admin.ModelAdmin):
    list_display = ["title", "vendor_image"]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Client)
admin.site.register(DeliveryAgent)
