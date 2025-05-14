from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from django.dispatch import receiver
from .models import (
    Product,
    CartItem,
    CartOrderItem,
    ShoppingCart,
    Wishlist,
    ClaimedOrder,
    CartOrder,
    CancellationRequestByDeliveryAgent,
    Notification,
    NotificationType,
    DeliveryAgent,
    ClientStrike,
    VendorStrike,
    DeliveryAgentStrike,
)
from django.core.exceptions import ValidationError
from userauths.models import User, Vendor, Client
import threading
import requests
import json
from django.contrib.contenttypes.models import ContentType
import os
from openai import OpenAI
from django.core.mail import send_mail


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# DEEPSEEK_API_KEY = (
#     "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"
# )


# client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


# def fetch_product_details(
#     product_id, product_title, product_description, category_name, sub_category_name
# ):
#     print("Signal to get product details is started....")

#     prompt = (
#         "You are an AI product assistant. Based on the following product information, "
#         "generate a detailed and informative product description that highlights its features, benefits, "
#         "and use cases. Include any relevant technical details and suggestions for ideal users.\n\n"
#         f"Product Title: {product_title}\n"
#         f"Subcategory: {sub_category_name}\n"
#         f"Category: {category_name}\n"
#         f"Short Description: {product_description}\n\n"
#         "Provide a full product description that includes technical specifications, user benefits, and ideal usage scenarios."
#     )

#     try:
#         response = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant"},
#                 {"role": "user", "content": prompt},
#             ],
#             stream=False,
#         )

#         details = response.choices[0].message.content.strip()

#         if details:
#             Product.objects.filter(id=product_id).update(details=details)
#             print("Product details successfully generated and saved.")

#         else:
#             print("No details return from the AI")

#     except Exception as e:
#         print(f"❌ Error occurred while generating product details: {e}")


def fetch_product_details(
    product_id, product_title, product_description, category_name, sub_category_name
):
    print("====================================================== signal started")

    prompt = (
        f"You are an AI product assistant. Based on the following product information"
        f"generate a detailed and informative product description that highlights its features, benefits, and use cases."
        f"Include any relevant technical details and suggestions for ideal users."
        f"Product Title: {product_title}"
        f"Subcategory: {sub_category_name}"
        f"Category: {category_name}"
        f"Short Description: {product_description}"
        f"Provide a full product description that includes technical specifications, user benefits, and ideal usage scenarios."
    )

    try:
        print("trying==============")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": "deepseek/deepseek-r1:free",
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )

        if response.status_code == 200:
            print("response is 200 ==================")
            response_data = response.json()
            details = (
                response_data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            print(details)
            print("finish details")

            if details:
                print("details exist !!")
                Product.objects.filter(id=product_id).update(details=details)
                print("it s saved successfully!!")

    except requests.exceptions.RequestException as e:
        print(f"error occurred while fetching the medicament details : {e}")


@receiver(post_save, sender=Product)
def check_stock(sender, instance, **kwargs):
    if instance.quantity < 1:
        # you should sender a notification and a warner to the vendor
        cart_items = instance.cart_items.all()
        for cart_item in cart_items:
            cart_item.is_active = False
            cart_item.save(update_fields=["is_active"])

        instance.in_stock = False
        instance.save(update_fields=["in_stock"])


@receiver(pre_save, sender=CartOrder)
def reduce_stock_after_vendor_confirmation(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        previous = CartOrder.objects.get(pk=instance.pk)

    except CartOrder.DoesNotExist:
        previous = None

    if (
        previous is not None
        and previous.order_status != "confirmed"
        and (
            instance.order_status == "confirmed" or instance.order_status == "delivered"
        )
    ):
        print("updating order status to confirmed")
        related_cart_order_items = instance.cart_order_items.all()
        for cart_order_item in related_cart_order_items:
            if cart_order_item.cart_item.product:
                cart_order_item.cart_item.product.quantity -= (
                    cart_order_item.cart_item.quantity
                )
                cart_order_item.cart_item.product.save(update_fields=["quantity"])


@receiver(post_save, sender=CartOrderItem)
def deactivate_cart_order_item_after_vendor_canceled(sender, instance, **kwargs):
    if instance.is_active and instance.is_canceled_by_vendor:
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        Notification.objects.create(
            user=instance.order.client.user,
            message=f"The vendor has canceled a cart order item",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification=NotificationType.CARTORDERITEM,
        )


# @receiver(pre_save, sender=CartOrderItem)
# def update_stock_after_client_cancel(sender, instance, **kwargs):
#     if instance.is_canceled:
#         quantity = instance.cart_item.quantity
#         instance.cart_item.product.quantity += quantity
#         instance.cart_item.product.save(update_fields=["quantity"])


@receiver(post_save, sender=Product)
def get_details(sender, instance, created, **kwargs):
    if created:
        if instance.title and instance.description:
            thread = threading.Thread(
                target=fetch_product_details,
                args=(
                    instance.id,
                    instance.title,
                    instance.description,
                    instance.sub_category.category.title,
                    instance.sub_category.title,
                ),
            )
            thread.daemon = True
            thread.start()

    # elif not instance.is_confirmed and instance.countdown is None:
    #     instance.cart_order_item.cart_item.is_active = True
    #     instance.cart_order_item.cart_item.product.quantity += (
    #         instance.cart_order_item.quantity
    #     )
    #     instance.cart_order_item.cart_item.save(update_fields=["is_active"])
    #     instance.cart_order_item.cart_item.product.save(update_fields=["quantity"])
    # TODO make sure to integrate the ai to generate bills or call back in their email


# @receiver(post_save, sender=CartOrderItem)
# def update_cart_item_status(sender, instance, created, **kwargs):
#     if created:
#         # product = instance.cart_item.product

#         if instance.cart_item.product.quantity < instance.quantity:
#             raise ValidationError("Insufficient stock for this product")

#         # product.quantity -= instance.quantity
#         # product.save(update_fields=["quantity"])
#         instance.cart_item.is_active = False
#         instance.cart_item.save(update_fields=["is_active"])

#         instance.total_price = (
#             instance.cart_item.product.price * instance.cart_item.quantity
#         )
#         instance.save(update_fields=["total_payed"])


# @receiver(pre_save, sender=CartItem)
# def check_stock_availability(sender, instance, **kwargs):
#     if instance.product.quantity < instance.quantity:
#         raise ValidationError(
#             "the quantity exceed the available stock , please adjust and lower the quantity !"
#         )


# @receiver(pre_save, sender=CartItem)
# def check_item_duplication(sender, instance, **kwargs):

#     if (
#         CartItem.objects.filter(shopping_cart=instance.shopping_cart, product=instance.product)
#         .exclude(pk=instance.pk)
#         .exists()
#     ):
#         raise ValidationError("the product exist already in your shopping cart")


# @receiver(post_save, sender=CartOrder)
# def calculate_total_payed_order(sender, instance, **kwargs):

#     cart_order_items = instance.cart_order_items.all()

#     if cart_order_items:
#         cart_order_total_payed = 0
#         for cart_order in cart_order_items:
#             cart_order_total_payed += cart_order.total_payed

#         instance.total_payed = cart_order_total_payed
#         instance.paid_status = cart_order_total_payed > 0
#         instance.save(update_fields=["total_payed", "paid_status"])


# @receiver(pre_save, sender=CartOrderItem)
# def check_cart_item_existence(sender, instance, **kwargs):

#     if not instance.cart_item:
#         raise ValidationError(
#             "a cart order item should be related to an existing cart item"
#         )

#     if instance.cart_item.is_active == False:
#         raise ValidationError(
#             "the cart item is inactive therefore you cannot make an order"
#         )


# @receiver(pre_save, sender=CartOrder)
# def prevent_modification_after_payment(sender, instance, **kwargs):
#     if instance.pk and instance.paid_status:
#         raise ValidationError("Paid orders cannot be modified")


# @receiver(post_save, sender=CartOrder)
# def check_one_vendor_per_order(sender, instance, **kwargs):

#     vendors = instance.cart_order_items.values_list(
#         "cart_item__product__vendor", flat=True
#     ).distinct()

#     if len(vendors) > 1:
#         raise ValidationError("The order cannot have more than one vendor !!")


# @receiver(pre_save, sender=Client)
# def check_client_existence(sender, instance, **kwargs):
#     user = instance.user
#     clients_objects = Client.objects.filter(user=user)

#     if clients_objects.count() > 1:
#         raise ValidationError("this user is already related to an existing client")


# @receiver(pre_save, sender=Vendor)
# def check_vendor_existence(sender, instance, **kwargs):
#     user = instance.user
#     vendor_objects = Vendor.objects.filter(user=user)

#     if vendor_objects.count() > 1:
#         raise ValidationError("this user is already related to an existing vendor")


@receiver(post_save, sender=Client)
def create_related_client_resources(sender, instance, created, **kwargs):
    if created:
        ShoppingCart.objects.get_or_create(client=instance)
        Wishlist.objects.get_or_create(client=instance)


# _save_in_progress = False
# @receiver(pre_save, sender=CartOrderItem)
# def check_cart_item_existence(sender, instance, **kwargs):
#     global _save_in_progress
#     if not instance.cart_item:
#         raise ValidationError("cart item is required")

#     instance.product = instance.cart_item.product
#     instance.save(update_fields=["product"])


# @receiver(pre_save, sender=Vendor)
# def check_if_user_is_admin(sender, instance, **kwargs):
#     if instance.user.is_staff:
#         raise ValidationError("this user is a staff user")


def cancel_and_notify_delivery_agent(claimed_order: ClaimedOrder):
    claimed_order.delivery_status = "canceled"
    claimed_order.save(update_fields=["delivery_status"])
    Notification.objects.create(
        user=claimed_order.delivery_agent.user,
        message=f"your order has been canceled , claimed order id : {claimed_order.id}, client name : {claimed_order.order.client.user.get_full_name()}, vendor name : {claimed_order.order.vendor.user.get_full_name()}",
        content_type=ContentType.objects.get_for_model(ClaimedOrder),
        object_id=claimed_order.id,
        notification_type=NotificationType.ORDER,
    )


@receiver(post_save, sender=CartOrder)
def cancel_cart_order_items(sender, instance, **kwargs):
    if instance.is_canceled and instance.is_active:
        CartOrder.objects.filter(pk=instance.pk).update(is_active=False)
        ClientStrike.objects.create(
            client=instance.client,
            reason="You have canceled an order",
        )
        related_cart_order_items = instance.cart_order_items.all()
        for cart_order_item in related_cart_order_items:
            cart_order_item.is_canceled = True
            cart_order_item.save(update_fields=["is_canceled"])

        claimed_order = (
            instance.claimed_orders.filter(is_failed=False)
            .exclude(delivery_status="delivered")
            .first()
        )

        if claimed_order:
            cancel_and_notify_delivery_agent(claimed_order)

        # TODO : create a strike for the client

    if instance.order_status == "canceled" and instance.is_active:
        CartOrder.objects.filter(pk=instance.pk).update(is_active=False)
        related_cart_order_items = instance.cart_order_items.all()
        for cart_order_item in related_cart_order_items:
            cart_order_item.is_canceled_by_vendor = True
            cart_order_item.save(update_fields=["is_canceled_by_vendor"])

        claimed_order = (
            instance.claimed_orders.filter(is_failed=False)
            .exclude(delivery_status="delivered")
            .first()
        )

        if claimed_order:
            cancel_and_notify_delivery_agent(claimed_order)

        # TODO : here i should update is canceled by vendor rather than is_canceled


# @receiver(post_save, sender=CartOrderItem)
# def incrementing_amount_of_cart_order_item_canceled(sender, instance, **kwargs):
#     if instance.is_canceled and instance.is_active:
#         client = instance.order.client
#         client.amount_of_canceled_cart_order_items += 1
#         client.save(update_fields=["amount_of_canceled_cart_order_items"])
#         instance.order.total_payed -= instance.total_payed
#         instance.is_active = False
#         instance.save(update_fields=["is_active"])
#         if client.amount_of_canceled_cart_order_items >= 10:
#             """ban the client for a month and send a strike"""
#             # TODO : send a notification as well
#         """create a client strike object"""
#         """notify the vendor that the client has canceled this cart order item"""
#     if instance.is_canceled_by_vendor and instance.is_active:
#         instance.is_active = False
#         # TODO : create a notification message
#         instance.save(update_fields=["is_active"])


@receiver(post_save, sender=CartOrderItem)
def readjust_amount_of_products_after_cancellation(sender, instance, **kwargs):
    if (instance.is_canceled or instance.is_canceled_by_vendor) and instance.is_active:
        instance.cart_item.product.quantity += instance.cart_item.quantity
        instance.cart_item.product.save(update_fields=["quantity"])
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        if instance.is_canceled:
            ClientStrike.objects.create(
                client=instance.order.client,
                reason="you have canceled a cart order item",
            )


@receiver(post_save, sender=Notification)
def send_an_email(sender, instance, created, **kwargs):
    if created:
        user_full_name = instance.user.get_full_name()
        user_email = instance.user.email
        message = instance.message
        send_mail(
            f"Hello, {user_full_name}",
            message,
            "mouadhoumada@gmail.com",
            [user_email],
            fail_silently=False,
        )


@receiver(post_save, sender=CancellationRequestByDeliveryAgent)
def check_if_cancellation_request_approved(sender, instance, **kwargs):
    if instance.is_approved and not instance.is_active:
        if instance.cancellation_reason == "CNR":
            instance.claimed_order.order.is_canceled = True
            instance.claimed_order.order.save(update_fields=["is_canceled"])
            instance.is_active = False
            instance.save(update_fields=["is_active"])


@receiver(post_save, sender=ClaimedOrder)
def update_order_status(sender, instance, **kwargs):
    if instance.delivery_status == "delivered":
        instance.order.order_status = "delivered"
        instance.is_active = False
        instance.order.save(update_fields=["order_status", "is_active"])


@receiver(post_save, sender=ClaimedOrder)
def create_notifications(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.order.client.user,
            message=f"A delivery agent has claimed your order : full name : {instance.delivery_agent.user.get_full_name()}",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification_type=NotificationType.ORDER,
        )

        Notification.objects.create(
            user=instance.order.vendor.user,
            message=f"A delivery agent has claimed an order of yours : full name : {instance.delivery_agent.user.get_full_name()}",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification_type=NotificationType.ORDER,
        )

        Notification.objects.create(
            user=instance.delivery_agent.user,
            message=f"Congratulations ! you have successfully claimed an order , you have 2 hours to get it from the vendor",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification_type=NotificationType.ORDER,
        )


@receiver(post_save, sender=CartOrder)
def sending_notification_to_vendor_client_delivery_agents(
    sender, instance, created, **kwargs
):
    if created:
        Notification.objects.create(
            user=instance.vendor.user,
            message=f"A new order has been placed",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification_type=NotificationType.ORDER,
        )

        Notification.objects.create(
            user=instance.client.user,
            message=f"Congratulations You have successfully placed a new order",
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            notification_type=NotificationType.ORDER,
        )

    if (
        instance.delivery_option
        and instance.order_status == "confirmed"
        and instance.is_active
        and not (ClaimedOrder.objects.filter(order=instance, is_failed=False))
    ):

        interested_delivery_agents = DeliveryAgent.objects.filter(
            city=instance.vendor.city
        )

        for delivery_agent in interested_delivery_agents:
            Notification.objects.create(
                user=delivery_agent.user,
                message=f"A new order is ready to be claimed",
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                notification_type=NotificationType.ORDER,
            )
