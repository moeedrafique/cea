# Generated by Django 5.1.2 on 2024-10-19 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0028_alter_memberchangerequest_new_dual_citizen'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='member_tddill',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
