# Generated by Django 5.1.2 on 2024-10-19 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0031_alter_member_member_till'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='member_till',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
