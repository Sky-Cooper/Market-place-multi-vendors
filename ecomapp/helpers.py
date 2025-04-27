from rest_framework import serializers


def is_valid_client_and_order(user, claimed_order):
    if not hasattr(user, "client"):
        raise serializers.ValidationError("only clients can create delivery ratings")

    if user.client != claimed_order.client:
        raise serializers.ValidationError("you dont own this order")
