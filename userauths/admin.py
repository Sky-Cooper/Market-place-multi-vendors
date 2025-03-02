from django.contrib import admin
from userauths.models import User, Vendor, Client


class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "first_name", "last_name", "is_active", "bio"]


class VendorAdmin(admin.ModelAdmin):
    list_display = ["title", "vendor_image"]


admin.site.register(User, UserAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Client)
