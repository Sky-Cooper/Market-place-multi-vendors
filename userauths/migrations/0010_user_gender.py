# Generated by Django 5.1.6 on 2025-05-02 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("userauths", "0009_deliveryagent_city"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="gender",
            field=models.CharField(
                choices=[("male", "Male"), ("female", "Female")],
                default="male",
                max_length=20,
            ),
        ),
    ]
