from django.contrib import admin
from userauths.models import User, Vendor, Client
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "is_active", "is_staff", "is_superuser")
    ordering = ("email",)

    def save_model(self, request, obj, form, change):
        if change:
            existing_user = User.objects.get(pk=obj.pk)
            if existing_user.password != obj.password:
                obj.set_password(obj.password)

            else:
                obj.set_password(obj.password)

            obj.save()


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "first_name", "last_name", "is_active", "bio"]


class VendorAdmin(admin.ModelAdmin):
    list_display = ["title", "vendor_image"]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Client)
