# Generated by Django 5.1.6 on 2025-04-26 19:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "ecomapp",
            "0012_rename_expiration_time_out_claimedorder_expiration_time_date_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="claimedorder",
            old_name="expiration_time_date",
            new_name="expiration_date_time",
        ),
    ]
