from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from phonenumber_field.modelfields import PhoneNumberField

MOROCCAN_CITIES_CHOICES = (("CS", "Casablanca"), ("RB", "Rabat"))


def user_directory_path(instance, filename):
    try:
        vid = instance.vendor.vid
    except AttributeError:
        vid = "unknown"
    return f"user_{vid}/{filename}"


class UserRoles(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    VENDOR = "VENDOR", "Vendor"
    CLIENT = "CLIENT", "Client"
    DELIVERY_AGENT = "Delivery_agent", "delivery_agent"


class ApplicationUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)

        if password is None:
            raise ValueError("the password must be provided!!")

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("role", UserRoles.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    uid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="u_")
    email = models.EmailField(unique=True, blank=False)
    role = models.CharField(max_length=20, choices=UserRoles.choices)
    username = models.CharField(max_length=100, unique=True, blank=False)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    is_active = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_image = models.ImageField(upload_to="profile_images", null=True, blank=True)
    phone_number = PhoneNumberField(region="MA", null=False, blank=False, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name} "


class Client(models.Model):
    cid = ShortUUIDField(unique=True, max_length=20, length=10, prefix="cli_")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client")
    list_of_interest = models.JSONField(default=list, null=True, blank=True)
    # TODO make sure that list of interest should be a separate model
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    amount_of_canceled_cart_order_items = models.PositiveBigIntegerField(default=0)

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
    image = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    address = models.CharField(max_length=255, blank=False)
    country = models.CharField(max_length=128, default="morocco")
    city = models.CharField(
        max_length=128,
        choices=MOROCCAN_CITIES_CHOICES,
        blank=False,
        null=False,
    )

    # make sure to handle the feature of the shipping time , it should be added

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    ban_expired_at = models.DateTimeField(null=True, blank=True)

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


MOROCCAN_CITIES_CHOICES = ()


class DeliveryAgent(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="delivery_agent"
    )
    city = models.CharField(
        max_length=56,
        choices=MOROCCAN_CITIES_CHOICES,
        null=False,
        blank=False,
        default="CS",
    )
    country = models.CharField(max_length=128, default="morocco")

    identity_picture = models.ImageField(
        upload_to="identity_pictures", null=False, blank=False
    )
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    ban_expired_at = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="delivery_agents/", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def today_failed_claims(self):
        pass

    def week_failed_claims(self):
        pass

    def month_failed_claims(self):
        pass

    def average_rating(self):
        pass

    class Meta:
        verbose_name = "Delivery Agent"
        verbose_name_plural = "Delivery Agents"

    def __str__(self):
        return f"delivery agent {self.user.get_full_name()}"
