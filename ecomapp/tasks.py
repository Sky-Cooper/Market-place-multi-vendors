from celery import shared_task
from django.utils import timezone
from .models import ClaimedOrder, Notification, DeliveryAgentStrike, NotificationType, DeliveryAgent, CartOrder
from django.contrib.contenttypes.models import ContentType


@shared_task
def check_and_fail_expired_claimed_orders():
    now = timezone.now()
    expired_claimed_orders = ClaimedOrder.objects.filter(expiration_date_time__lte = now, is_confirmed_by_vendor = False, is_failed=False)
    for claimed_order in expired_claimed_orders:     
        claimed_order.is_failed = True
        claimed_order.save()
        Notification.objects.create(
            user = claimed_order.order.vendor.user,
            message = f"The delivery agent : {claimed_order.delivery_agent.user.get_full_name()} has failed reaching you to get the order",
            content_type= ContentType.objects.get_for_model(ClaimedOrder),
            object_id = claimed_order.id,
            notification_type = NotificationType.CLAIMEDORDER
        )

        Notification.objects.create(
            user = claimed_order.delivery_agent.user,
            message = f"You have failed in getting the order , therefore you are receiving a strike",
            content_type = ContentType.objects.get_for_model(ClaimedOrder),
            object_id = claimed_order.id,
            notification_type = NotificationType.CLAIMEDORDER
        )

        DeliveryAgentStrike.objects.create(
            delivery_agent = claimed_order.delivery_agent,
            reason = f"You have failed to get the order from the vendor in less than 2 hours, vendor owner name : {claimed_order.order.vendor.user.get_full_name()}",
            
        )

        interested_delivery_agents = DeliveryAgent.objects.filter(city=claimed_order.order.vendor.city).exclude(pk=claimed_order.delivery_agent.pk)
        for delivery_agent in interested_delivery_agents:
            Notification.objects.create(
                user = delivery_agent.user,
                message = f"A new order ready to be claimed, hurry up and get it",
                content_type = ContentType.objects.get_for_model(CartOrder),
                object_id = claimed_order.order.id,
                notification_type = NotificationType.CLAIMEDORDER
            )


