from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User, user_directory_path, Client, Vendor
from taggit.managers import TaggableManager
from datetime import timedelta


# Create your models here.


STATUS_CHOICES = (
    ("process", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ("returned", "Returned"),
)

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


class Category(models.Model):
    cid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="cat_",
        alphabet="abcdefghijklmn12345",
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
    scid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="subcat_")
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = models.ImageField(upload_to="subcategories/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="sub_categories"
    )


class Product(models.Model):
    pid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="pro_",
        alphabet="abcdefghijklmn12345",
    )

    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="products"
    )
    title = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
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
    quantity = models.PositiveIntegerField(default=1, blank=False)
    potential_delivery_days = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Products"

    def get_tags(self):
        return self.tags.names()

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title

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

        return f"{self.client.user.username} - {self.product.title} - {self.comment} - {self.rating}"


class Wishlist(models.Model):
    wid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="wish_",
        alphabet="abcdefghjkl12345",
    )
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="wishlist"
    )
    products = models.ManyToManyField(
        Product,
        related_name="wishlists",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "wishlists"

    def __str__(self):
        return f"wish list of {self.client.user.username}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address = models.CharField(max_length=524, blank=False)
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"address for {self.user.get_full_name()}"


class ShoppingCart(models.Model):
    sid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="cart_",
        alphabet="abcdefghijklmn12345",
    )
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
    ciid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="cart_item_",
        alphabet="abcdefghijklmn12345",
    )
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
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"cart item : {self.product.title} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


# incases the payment is cash on delivery then the vendor should follow the structure of the shipping for better stock management
# the structure is the following, as we said in case the order has been delivered successfully then the vendor should go to his dashboard
# and he should go to the orders that been created for his product and he should go to the shipping status and adjust it to true


class GlobalOrder(models.Model):
    gid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="glo_")
    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE, related_name="global_orders"
    )  # i created this model in order to have one global order which has all the products the client payed and then we will create many cartorders depending ont he vendors of each product

    class Meta:
        verbose_name_plural = "global_orders"

    def __str__(self):
        return f"Global order for {self.shopping_cart.client}"


class CartOrder(models.Model):
    oid = ShortUUIDField(
        unique=True,
        length=10,
        max_length=20,
        prefix="cart_order_",
        alphabet="abcdefghijklmn12345",
    )
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="client_orders"
    )  # im not deleting because i wanna keep the order object for the analysis of the vendor
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="vendor_orders", null=True
    )  # im not deleting because i wanna keep the history of purchases for the client, null true because as far as i know after the client payed ,first it will create a cart order but it would not be related to any vendor untill we crete order cart items and then we will make sure that all of theses order cart items has the same vendor before attributing the vendor to this order
    total_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="processing"
    )
    is_canceled = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="cod"
    )

    global_order = models.ForeignKey(
        GlobalOrder, on_delete=models.CASCADE, related_name="cart_orders"
    )

    class Meta:
        verbose_name_plural = "Cart Orders"

    def __str__(self):
        vendor_name = self.vendor.user.username if self.vendor else "No vendor yet"
        return f"Order: {self.oid} - client :  {self.client.user.username} vendor : {vendor_name}"


class CartOrderItem(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cart_order_items"
    )
    coiid = ShortUUIDField(
        unique=True, length=10, max_length=20, prefix="cart_order_items"
    )
    order = models.ForeignKey(
        CartOrder, on_delete=models.CASCADE, related_name="cart_order_items"
    )
    cart_item = models.OneToOneField(
        CartItem, on_delete=models.CASCADE, related_name="cart_order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    total_payed = models.DecimalField(max_digits=10, decimal_places=2)
    facture = models.CharField(max_length=524, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cart_order_item_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="processing"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_order_items"
    )  # i ll make sure to create a whole system that manage the delivery taking in consideration the exceptions that could happen due fraud or scam
    potential_delivery_days = models.PositiveBigIntegerField(null=True, blank=True)
    is_canceled = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Cart Order Items"

    def __str__(self):
        return f"{self.cart_item.product.title} {self.quantity}"

    def save(self, *args, **kwargs):
        if self.cart_item:
            self.quantity = self.cart_item.quantity

        potential_delivery_days_product = self.cart_item.product.potential_delivery_days
        if potential_delivery_days_product is not None:
            self.potential_delivery_days = potential_delivery_days_product

        super().save(*args, **kwargs)


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
