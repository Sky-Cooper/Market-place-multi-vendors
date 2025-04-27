from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import (
    User,
    user_directory_path,
    Client,
    Vendor,
    DeliveryAgent,
    MOROCCAN_CITIES_CHOICES,
)
from taggit.managers import TaggableManager
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import TextChoices

# Create your models here.


STATUS_CHOICES = (
    ("process", "Processing"),
    ("confirmed", "Confirmed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("canceled", "Canceled"),
    ("returned", "Returned"),
)

SUPPORT_LEVEL = (("standard", "Standard"), ("high", "Hight"), ("advanced", "Advanced"))


STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("in_review", "In_review"),
    ("rejected", "Rejected"),
    ("published", "Published"),
)

RATING_CHOICES = (
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
)


PAYMENT_CHOICES = (("cod", "Cash on delivery"), ("online", "Online"))

PLAN_CHOICES = (("basic", "Basic"), ("standard", "Standard"), ("premium", "Premium"))


class Sector(models.Model):
    title = models.CharField(max_length=128, null=False, blank=False, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to="sectors/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Sectors"

    def __str__(self):
        return self.title


class Category(models.Model):
    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, related_name="categories"
    )
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = models.ImageField(upload_to="category/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50" /> ' % (self.image.url))

    def __str__(self):
        return self.title


class SubCategory(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = models.ImageField(upload_to="subcategories/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="sub_categories"
    )

    def __str__(self):
        return f"sub category :{self.title} id :{self.id}"


class SubCategoryTag(models.Model):
    name = models.CharField(max_length=50)
    SubCategory = models.ManyToManyField(SubCategory, related_name="tags")

    def __str__(self):
        return f"{self.name}"


class Product(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="products"
    )
    title = models.CharField(max_length=128)
    description = models.TextField(null=False, blank=False, default="")
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, related_name="products"
    )
    image = models.ImageField(upload_to=user_directory_path)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False)
    old_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    specifications = models.TextField(null=True, blank=True)
    tags = TaggableManager()
    product_status = models.CharField(
        max_length=20, choices=STATUS, default="in_review"
    )
    is_active = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    details = models.TextField(null=True, blank=True)
    potential_guarantee_period = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Products"

    def get_tags(self):
        return self.tags.names()

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return f"title {self.title} id : {self.id}"

    def save(self, *args, **kwargs):
        if self.old_price and self.old_price > self.price:
            discount = self.old_price - self.price
            discount = discount / self.old_price * 100
            self.discount_percentage = round(discount)

        if self.old_price and self.old_price < self.price:
            discount = 0

        if self.quantity == 0:
            self.in_stock = False

        elif self.quantity > 0:
            self.in_stock = True

        super().save(*args, **kwargs)


class ProductImages(models.Model):
    image = models.ImageField(upload_to="product-images/")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )

    class Meta:
        verbose_name_plural = "Product Images"

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return f"image for {self.product.title}"


class ProductReview(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    comment = models.TextField(max_length=524, blank=True, null=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Product Reviews"

    def __str__(self):

        return f"{self.client.user.get_full_name()} - {self.product.title} - {self.comment} - {self.rating}"


class Wishlist(models.Model):
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="wishlist"
    )
    products = models.ManyToManyField(
        Product,
        related_name="wishlists",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "wishlists"

    def __str__(self):
        return f"wish list of {self.client.user.get_full_name()} id {self.id}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.CharField(max_length=524, blank=False)
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"address for {self.user.get_full_name()}"


class ShoppingCart(models.Model):
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shopping Carts"

    def __str__(self):
        return f"Shopping cart of {self.client.user.get_full_name()}"


class CartItem(models.Model):
    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE, related_name="cart_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_ordered = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Cart Items"
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["shopping_cart", "product"], name="unique_product_in_cart"
        #     )
        # ]

    def __str__(self):
        return f"cart item id {self.id}: {self.product.title} - {self.quantity}"

    def save(self, *args, **kwargs):
        if self.product and self.quantity:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


# incases the payment is cash on delivery then the vendor should follow the structure of the shipping for better stock management
# the structure is the following, as we said in case the order has been delivered successfully then the vendor should go to his dashboard
# and he should go to the orders that been created for his product and he should go to the shipping status and adjust it to true


class GlobalOrder(models.Model):

    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE, related_name="global_orders"
    )  # i created this model in order to have one global order which has all the products the client payed and then we will create many cartorders depending ont he vendors of each product
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, default="cod"
    )
    address = models.TextField(blank=False, null=False, default="Casablanca")
    # TODO : make sure to remove the default value of the address
    city = models.CharField(
        max_length=56,
        choices=MOROCCAN_CITIES_CHOICES,
        default="Casablanca",
        null=False,
        blank=False,
    )
    country = models.CharField(
        max_length=56, null=False, blank=False, default="Morocco"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_option = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "global_orders"

    def __str__(self):
        return f"Global order for {self.shopping_cart.client.user.get_full_name()}"


class CartOrder(models.Model):

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="client_orders"
    )  # im not deleting because i wanna keep the order object for the analysis of the vendor
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="vendor_orders", null=True
    )  # im not deleting because i wanna keep the history of purchases for the client, null true because as far as i know after the client payed ,first it will create a cart order but it would not be related to any vendor untill we crete order cart items and then we will make sure that all of theses order cart items has the same vendor before attributing the vendor to this order
    total_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="cod"
    )

    global_order = models.ForeignKey(
        GlobalOrder, on_delete=models.CASCADE, related_name="cart_orders"
    )
    delivery_option = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    order_status = models.CharField(
        max_length=128, choices=STATUS_CHOICES, default="processing"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cart Orders"

    def __str__(self):
        vendor_name = (
            self.vendor.user.get_full_name() if self.vendor else "No vendor yet"
        )
        return f"Order: {self.id} - client :  {self.client.user.get_full_name()} vendor : {vendor_name}"


class CartOrderItem(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cart_order_items"
    )

    order = models.ForeignKey(
        CartOrder, on_delete=models.CASCADE, related_name="cart_order_items"
    )
    cart_item = models.OneToOneField(
        CartItem, on_delete=models.CASCADE, related_name="cart_order_items"
    )

    total_payed = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # cart_order_item_status = models.CharField(
    #     max_length=20, choices=STATUS_CHOICES, default="processing"
    # )
    # i ll make sure to create a whole system that manage the delivery taking in consideration the exceptions that could happen due fraud or scam
    is_canceled_by_vendor = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cart Order Items"

    def __str__(self):
        return f"{self.cart_item.product.title} {self.cart_item.quantity}"


# class OrderConfirmationVendor(models.Model):
#     is_confirmed = models.BooleanField(default=False)
#     cart_order_item = models.OneToOneField(
#         CartOrderItem, on_delete=models.CASCADE, related_name="confirmation"
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     countdown = models.DateTimeField(null=True, blank=True)

#     def save(self, *args, **kwargs):
#         if not self.countdown:
#             self.countdown = self.created_at + timedelta(days=2)
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"status  - {self.is_confirmed} - cart order item : {self.cart_order_item.cart_item.product} "


class SubscriptionPlan(models.Model):
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, blank=False
    )
    title = models.CharField(
        max_length=20, choices=PLAN_CHOICES, null=False, blank=False
    )
    description = models.TextField()
    max_products = models.PositiveBigIntegerField(default=50)
    support_level = models.CharField(
        max_length=20, choices=SUPPORT_LEVEL, default="standard"
    )

    def __str__(self):
        return f"{self.title}"


class Subscription(models.Model):
    vendor = models.OneToOneField(
        Vendor, on_delete=models.CASCADE, related_name="subscription"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscriptions",
    )
    expired_at = models.DateTimeField(null=True, blank=True)
    total_payed = models.DecimalField(
        max_digits=20, decimal_places=2, null=False, blank=False
    )
    is_canceled = models.BooleanField(default=False)

    # TODO : make sure to add a foreign key in the vendor
    # TODO : make sure at the end to check in every single action the vendor attempt to do to check weather or not their subscription is expired
    # TODO : make sure to implement is expired method

    def is_expired(self):
        if not self.expired_at:
            return False
        return timezone.now() > self.expired_at

    def __str__(self):
        return f"{self.id}  vendor {self.vendor}"


class SubscriptionFeature(models.Model):
    title = models.CharField(max_length=120, null=False, blank=False)
    description = models.TextField()
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.CASCADE, related_name="features"
    )

    def __str__(self):
        return f"{self.title}"


class SubscriptionPayment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount_payed = models.DecimalField(
        max_digits=10, decimal_places=2, null=False, blank=False
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, related_name="payments"
    )

    def __str__(self):
        return f"subscription payments {self.id}"


DELIVERY_CHOICES = (
    ("processing", "Processing"),
    ("claimed from vendor", "Claimed from vendor"),
    ("on the way to destination", "On the way to destination"),
    ("delivered", "Delivered"),
    ("returned", "Returned"),
    ("canceled", "Canceled"),
)


class ClaimedOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_agent = models.ForeignKey(
        DeliveryAgent,
        on_delete=models.SET_NULL,
        null=True,
        related_name="claimed_order",
    )
    order = models.ForeignKey(
        CartOrder, on_delete=models.CASCADE, related_name="claimed_orders"
    )
    is_confirmed_by_vendor = models.BooleanField(default=False)
    expiration_date_time = models.DateTimeField(null=True, blank=True)
    is_failed = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=56, choices=DELIVERY_CHOICES, default="processing"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(is_failed=False),
                name="unique_claim_per_order",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.expiration_date_time:
            self.expiration_date_time = timezone.now() + timedelta(hours=2)

        return super().save(*args, **kwargs)

    def mark_as_failed_if_time_out(self):
        current_datetime = timezone.now()

        if (
            current_datetime > self.expiration_time_out
            and not self.is_confirmed_by_vendor
        ):
            self.is_failed = True
            self.save(update_fields=["is_failed"])
            return True

    def __str__(self):
        try:
            return f"claim by {self.delivery_agent.user.get_full_name()}"
        except AttributeError:
            return f"claim {self.id} has no delivery agent"


CANCELLATION_REASONS = (
    ("VNR", "vendor is not reachable"),
    ("CNR", "client is not reachable"),
    ("ANR", "delivery agent is not reachable"),
    ("OTHERS", "others"),
)


class CancellationRequestByDeliveryAgent(models.Model):
    cancellation_reason = models.CharField(
        max_length=128, choices=CANCELLATION_REASONS, null=False, blank=False
    )
    is_approved = models.BooleanField(default=False)
    claimed_order = models.OneToOneField(
        ClaimedOrder,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cancellation_request",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"cancellation request by delivery agent id : {self.id}"


class DeliveryRating(models.Model):
    claimed_order = models.OneToOneField(
        ClaimedOrder, on_delete=models.CASCADE, related_name="delivery_rating"
    )
    rating = models.PositiveIntegerField(
        validators=[MaxValueValidator(5)], null=False, blank=False
    )
    comment = models.TextField()
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, related_name="delivery_rating"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"delivery rating id : {self.id}, by client {self.client.user.get_full_name()} to delivery agent {self.claimed_order.delivery_agent.user.get_full_name()}"


class DeliveryAgentStrike(models.Model):
    delivery_agent = models.ForeignKey(
        DeliveryAgent, on_delete=models.CASCADE, related_name="strikes"
    )
    reason = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"strike id : {self.id}, reason : {self.reason}, delivery agent : {self.delivery_agent.user.get_full_name()}"


class VendorStrike(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="strikes")
    reason = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"strike id: {self.id}, vendor : {self.vendor.user.get_full_name()}"


class ClientStrike(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="strikes")
    reason = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"strike id : {self.id}, client: {self.client.user.get_full_name()}"


class NotificationType(TextChoices):
    ORDER = "order", "Order"
    MESSAGE = "message", "Message"
    CARTORDERITEM = "cart_order_item", "Cart_order_item"
    CLAIMEDORDER = "claimed_order", "Claimed_order"


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=128, choices=NotificationType.choices, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"notification {self.id}, user : {self.user.get_full_name()}"


class FullSizeImages(models.Model):
    pass
