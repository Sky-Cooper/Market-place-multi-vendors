from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe


def user_directory_path(instance, filename):
    vendor_id = getattr(instance, "vendor", None)
    return f"user_{vendor_id.vid if vendor_id else 'unknown'}/{filename}"


class UserRoles(models.TextChoices):
    CLIENT = (
        "client",
        "Client",
    )
    VENDOR = (
        "vendor",
        "Vendor",
    )
    ADMIN = (
        "admin",
        "admin",
    )
    SUPERADMIN = "superadmin", "Superadmin"


class ApplicationUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)

        if password is None:
            raise ValueError("the password must be provided!!")

        if password:
            user.set_password(password)

        user.save(using=self._db)

        # if role == UserRoles.CLIENT:
        #     Client.objects.create(user=user)

        # elif role == UserRoles.VENDOR:
        #     required_fields = ["title", "address", "contact", "image"]
        #     missing_fields = [
        #         field for field in required_fields if field not in extra_fields
        #     ]
        #     if missing_fields:
        #         raise ValueError(
        #             f"the vendor did not fill the required fields , make sure to fill {', '.join(missing_fields)}"
        #         )

        #     Vendor.objects.create(
        #         user=user,
        #         title=extra_fields.get("title", ""),
        #         address=extra_fields.get("address", ""),
        #         contact=extra_fields.get("contact", ""),
        #         image=extra_fields.get("image", None),
        #         description=extra_fields.get("description", ""),
        #         shipping_time=extra_fields.get("shipping_time", None),
        #         guarantee_period=extra_fields.get("guarantee_period", "No guarantee"),
        #     )

        return user


class User(AbstractUser):
    uid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="u_")
    email = models.EmailField(unique=True, blank=False)
    username = models.CharField(max_length=100, unique=True, blank=False)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    is_active = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.username


class Client(models.Model):
    cid = ShortUUIDField(unique=True, max_length=20, length=10, prefix="cli_")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    list_of_interest = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)

    # the list_of_interest field gonna with the following : i ll display the possible categories and sub categories that exist in the database , and within the process of registration, the user gonna select some of the options and these options must be stored in his client instance in the database in this field list_of_interest , example ["food", "cloths", "classic_cloths" ...]
    def __str__(self):
        return f"client : {self.user.username}"


class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor")

    vid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="ven_",
        alphabet="abcdefghijklmn12345",
    )

    title = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to=user_directory_path)
    address = models.CharField(max_length=255, blank=False)
    contact = models.CharField(max_length=20, blank=False, unique=True)
    shipping_time = models.PositiveIntegerField(blank=False, null=False)
    # make sure to handle the feature of the shipping time , it should be added
    guarantee_period = models.CharField(max_length=100, default="No guarantee")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)

    @property
    def chat_response_time(self):
        return 10

    @property
    def average_rating(self):
        return 10

    class Meta:
        verbose_name_plural = "Vendors"

    def vendor_image(self):
        if self.image:

            return mark_safe(
                '<img src="%s" width="50" height="50" />' % (self.image.url)
            )

    def __str__(self):
        return self.title
