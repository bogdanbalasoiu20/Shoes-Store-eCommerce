# Generated by Django 5.1.1 on 2024-12-10 20:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_discountcode_lucky_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='discountcode',
            name='lucky_user',
        ),
    ]
