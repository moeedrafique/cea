# Generated by Django 5.1.2 on 2024-10-19 14:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0029_member_member_tddill'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='member_tddill',
            new_name='member_till',
        ),
    ]
