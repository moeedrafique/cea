# Generated by Django 5.1.2 on 2024-10-17 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0018_alter_member_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='fee',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
    ]
