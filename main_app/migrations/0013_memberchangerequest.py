# Generated by Django 5.1.2 on 2024-10-17 01:51

import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0012_remove_payment_branch_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberChangeRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changes', models.JSONField(default=dict)),
                ('new_full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('new_father_name', models.CharField(blank=True, max_length=255, null=True)),
                ('new_cnic', models.CharField(blank=True, max_length=13, null=True)),
                ('new_dob', models.DateField(blank=True, null=True)),
                ('new_gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=10, null=True)),
                ('new_nic_type', models.CharField(blank=True, choices=[('cnic', 'CNIC'), ('nicop', 'NICOP')], max_length=50, null=True)),
                ('new_country_of_stay', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('new_present_address', models.TextField(blank=True, null=True)),
                ('new_permanent_address', models.TextField(blank=True, null=True)),
                ('new_dual_citizen', models.BooleanField(blank=True, choices=[(True, 'Yes'), (False, 'No')], null=True)),
                ('new_other_citizenship', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('new_pri_mob', models.CharField(blank=True, max_length=15, null=True)),
                ('new_sec_mob', models.CharField(blank=True, max_length=15, null=True)),
                ('new_designation', models.CharField(blank=True, max_length=100, null=True)),
                ('new_business_name', models.CharField(blank=True, max_length=255, null=True)),
                ('new_business_address', models.TextField(blank=True, null=True)),
                ('new_pri_land', models.CharField(blank=True, max_length=15, null=True)),
                ('new_sec_land', models.CharField(blank=True, max_length=15, null=True)),
                ('new_employee_number', models.CharField(blank=True, max_length=20, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_rejected', models.BooleanField(default=False)),
                ('submission_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('admin_reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='change_requests', to='main_app.member')),
                ('new_district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main_app.district')),
                ('new_tehsil', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main_app.tehsil')),
            ],
        ),
    ]
