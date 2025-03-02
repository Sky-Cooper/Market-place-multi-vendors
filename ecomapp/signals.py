from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from django.dispatch import receiver
from .models import *
from django.core.exceptions import ValidationError
from userauths.models import User, Vendor, Client


@receiver(post_save, sender=Product)
def check_stock(sender, instance, **kwargs):
    if instance.quantity == 0 and instance.is_active:
        instance.is_active = False
        # you should sender a notification and a warner to the vendor
        instance.save(update_fields=["is_active"])

        cart_items = instance.cart_items.all()
        for cart_item in cart_items:
            cart_item.is_active = False
            cart_item.save(update_fields=["is_active"])


@receiver(post_save, sender=OrderConfirmationVendor)
def reduce_stock_after_vendor_confirmation(sender, instance, **kwargs):
    if instance.is_confirmed:
        instance.cart_order_item.cart_item.product.quantity -= (
            instance.cart_order_item.quantity
        )
        instance.cart_order_item.cart_item.product.save(update_fields=["quantity"])

    elif not instance.is_confirmed and instance.countdown is None:
        instance.cart_order_item.cart_item.is_active = True
        instance.cart_order_item.cart_item.product.quantity += (
            instance.cart_order_item.quantity
        )
        instance.cart_order_item.cart_item.save(update_fields=["is_active"])
        instance.cart_order_item.cart_item.product.save(update_fields=["quantity"])


@receiver(post_save, sender=CartOrderItem)
def update_cart_item_status(sender, instance, created, **kwargs):
    if created:
        # product = instance.cart_item.product

        if instance.cart_item.product.quantity < instance.quantity:
            raise ValidationError("Insufficient stock for this product")

        # product.quantity -= instance.quantity
        # product.save(update_fields=["quantity"])
        instance.cart_item.is_active = False
        instance.cart_item.save(update_fields=["is_active"])

        instance.total_price = (
            instance.cart_item.product.price * instance.cart_item.quantity
        )
        instance.save(update_fields=["total_payed"])


@receiver(pre_save, sender=CartItem)
def check_stock_availability(sender, instance, **kwargs):
    if instance.product.quantity < instance.quantity:
        raise ValidationError(
            "the quantity exceed the available stock , please adjust and lower the quantity !"
        )


@receiver(pre_save, sender=CartItem)
def check_item_duplication(sender, instance, **kwargs):
    shopping_cart = instance.shopping_cart
    product = instance.product
    if (
        CartItem.objects.filter(shopping_cart=shopping_cart, product=product)
        .exclude(pk=instance.pk)
        .exists()
    ):
        raise ValidationError("the product exist already in your shopping cart")


@receiver(post_save, sender=CartOrder)
def calculate_total_payed_order(sender, instance, **kwargs):

    cart_order_items = instance.cart_order_items.all()

    if cart_order_items:
        cart_order_total_payed = 0
        for cart_order in cart_order_items:
            cart_order_total_payed += cart_order.total_payed

        instance.total_payed = cart_order_total_payed
        instance.paid_status = cart_order_total_payed > 0
        instance.save(update_fields=["total_payed", "paid_status"])


@receiver(pre_save, sender=CartOrderItem)
def check_cart_item_existence(sender, instance, **kwargs):

    if not instance.cart_item.exists():
        raise ValidationError(
            "a cart order item should be related to an existing cart item"
        )

    if instance.cart_item.is_active == False:
        raise ValidationError(
            "the cart item is inactive therefore you cannot make an order"
        )


@receiver(pre_save, sender=CartOrder)
def prevent_modification_after_payment(sender, instance, **kwargs):
    if instance.pk and instance.paid_status:
        raise ValidationError("Paid orders cannot be modified")


@receiver(pre_save, sender=CartOrder)
def check_one_vendor_per_order(sender, instance, **kwargs):

    vendors = instance.cart_order_items.values_list(
        "cart_item__product__vendor", flat=True
    ).distinct()

    if len(vendors) > 1:
        raise ValidationError("The order cannot have more than one vendor !!")


@receiver(pre_save, sender=Client)
def check_client_existence(sender, instance, **kwargs):
    user = instance.user
    clients_objects = Client.objects.filter(user=user)

    if clients_objects.count() > 1:
        raise ValidationError("this user is already related to an existing client")


@receiver(pre_save, sender=Vendor)
def check_vendor_existence(sender, instance, **kwargs):
    user = instance.user
    vendor_objects = Vendor.objects.filter(user=user)

    if vendor_objects.count() > 1:
        raise ValidationError("this user is already related to an existing vendor")


@receiver(post_save, sender=Client)
def create_shopping_cart(sender, instance, created, **kwargs):
    if created:
        ShoppingCart.objects.create(client=instance)


@receiver(pre_save, sender=CartOrderItem)
def check_cart_item_existence(sender, instance, **kwargs):
    if not instance.cart_item:
        raise ValidationError("cart item is required")

    instance.product = instance.cart_item.product
    instance.save(update_fields=["product"])
