from django.contrib import admin
from django import forms
# Register your models here.
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin

from .models import *

# Register Member model
from .resources import TehsilResource, DistrictResource


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'cnic', 'dob', 'gender', 'nic_type', 'country_of_stay', 'dual_citizen', 'business_name')
    search_fields = ('full_name', 'cnic', 'business_name')
    list_filter = ('gender', 'nic_type', 'country_of_stay', 'dual_citizen')
    readonly_fields = ('cnic_last_digits',)
    # fieldsets = (
    #     ('Personal Information', {
    #         'fields': ('full_name', 'father_name', 'cnic', 'dob', 'gender', 'nic_type', 'country_of_stay',
    #                    'present_address', 'permanent_address', 'dual_citizen', 'pri_mob', 'other_citizenship', 'sec_mob', 'picture')
    #     }),
    #     ('Business Information', {
    #         'fields': ('designation', 'business_name', 'business_address', 'tehsil', 'district',
    #                    'pri_land', 'employee_number', 'sec_land')
    #     }),
    # )

    def cnic_last_digits(self, obj):
        return obj.cnic_last_digits()
    cnic_last_digits.short_description = 'CNIC Last 4 Digits'

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'role', 'currency_association_id']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'currency_association_id')}),
    )
@admin.register(Tehsil)
class TehsilAdmin(ImportExportModelAdmin):
    resource_class = TehsilResource
    list_display = ('name', 'district', 'latitude', 'longitude')  # Customize columns displayed in admin
admin.site.register(User, CustomUserAdmin)

@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):
    resource_class = DistrictResource
    list_display = ('name',)  # Customize columns displayed in admin


class FeeAdmin(admin.ModelAdmin):
    list_display = ('member', 'fee_type', 'amount_submitted', 'amount_remaining', 'is_approved', 'renewal_date')
    search_fields = ('member__full_name', 'fee_type', 'application_id')
    list_filter = ('fee_type', 'submission_method', 'is_approved')

admin.site.register(Fee, FeeAdmin)

admin.site.register(Payment)
admin.site.register(MemberChangeRequest)
