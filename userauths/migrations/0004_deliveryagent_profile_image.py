# Generated by Django 5.1.6 on 2025-04-24 01:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("userauths", "0003_alter_deliveryagent_city"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliveryagent",
            name="profile_image",
            field=models.ImageField(blank=True, null=True, upload_to="delivery_agents"),
        ),
    ]
