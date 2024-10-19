from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django_countries import countries

from .encryption_util import encrypt_data, decrypt_data  # Import the utility functions
from django_countries.fields import CountryField
# Custom User model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('member', 'Member'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    currency_association_id = models.CharField(max_length=20, unique=True)

# Tehsil and District models
class District(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Tehsil(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.district.name}"
class Payment(models.Model):
    SUBMISSION_METHODS = [
        ('cash', 'By Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    submission_method = models.CharField(max_length=50, choices=SUBMISSION_METHODS)

    # Additional fields
    title = models.CharField(max_length=255, blank=True, null=True)  # Payment title or description

    # Bank transfer-specific fields
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    iban = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.title or self.submission_method}"

class Fee(models.Model):
    FEE_TYPES = [
        ('new registration', 'New Registration'),
        ('renewal', 'Renewal'),
        ('change of information', 'Change of Information'),
        ('transfer of ownership', 'Transfer of Ownership'),
        ('transfer of ownership (DEATH OF ORIGINAL OWNER)', 'Transfer of Ownership (DEATH OF ORIGINAL OWNER)'),
    ]
    SUBMISSION_METHODS = [
        ('cash', 'By Cash'),
        ('bank transfer', 'Bank Transfer'),
    ]

    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    fee_type = models.CharField(max_length=50, choices=FEE_TYPES)
    submission_method = models.CharField(max_length=50, choices=SUBMISSION_METHODS)
    amount_submitted = models.DecimalField(max_digits=10, decimal_places=2)
    amount_remaining = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    # Link to the Payment model
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE)  # Change from OneToOneField to ForeignKey
    renewal_date = models.DateField(default=timezone.now)  # Track when the fee was submitted
    is_approved = models.BooleanField(default=False)  # Approved by admin
    # application_id = models.CharField(max_length=100, default=None, null=True, blank=True)

    def __str__(self):
        return f"{self.fee_type}"


class Member(models.Model):
    application_id = models.CharField(max_length=25, unique=True, null=True, blank=True)  # Ensure uniqueness
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, default=None)
    father_name = models.CharField(max_length=255, default=None)
    cnic = models.CharField(max_length=13, unique=True, default=None)
    dob = models.DateField(default=None)

    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], default=None)

    NIC_TYPE_CHOICES = [
        ('cnic', 'CNIC'),
        ('nicop', 'NICOP'),
    ]
    nic_type = models.CharField(max_length=50, choices=NIC_TYPE_CHOICES, default=None)

    # CountryField for country_of_stay
    country_of_stay = CountryField(blank_label='Select Country', default='PK')  # 'PK' for Pakistan

    present_address = models.TextField(default=None)
    permanent_address = models.TextField(default=None)

    DUAL_CITIZEN_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    dual_citizen = models.CharField(
        max_length=3,
        default='no',
        blank=True, null=True
    )
    other_citizenship = CountryField(blank=True, null=True)
    pri_mob = models.CharField(max_length=15, default=None)
    sec_mob = models.CharField(max_length=15, null=True, blank=True)
    picture = models.ImageField(upload_to='member_pics/', null=True, blank=True)

    # Business Information
    designation = models.CharField(max_length=100, default="Member")
    business_name = models.CharField(max_length=255, default=None)
    business_address = models.TextField(default=None)

    # Foreign Keys for Tehsil and District
    tehsil = models.ForeignKey('Tehsil', on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True)

    pri_land = models.CharField(max_length=15, null=True, blank=True)
    employee_number = models.CharField(max_length=20, default=None)
    sec_land = models.CharField(max_length=15, null=True, blank=True)

    # New fields for approval and status
    is_approved = models.BooleanField(default=False)  # Approved by admin
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', null=True)  # Member status
    # Field to store the approval time
    joined_at = models.DateTimeField(null=True, blank=True)  # Will be set when the member is approved
    created_at = models.DateTimeField(auto_now_add=True)
    member_till = models.DateField(default=None, null=True, blank=True)  # Field to track membership expiry date

    def __str__(self):
        return f"{self.full_name} ({self.cnic})"

    def save(self, *args, **kwargs):
        # If the member is approved and joined_at is not already set
        if self.is_approved and self.joined_at is None:
            self.joined_at = timezone.now()  # Set the current time as the join date

        super(Member, self).save(*args, **kwargs)

    def cnic_last_digits(self):
        # Return the last four digits of the CNIC
        if self.cnic:
            return self.cnic[-4:]
        return ''


class MemberChangeRequest(models.Model):
    # Add this field for application ID
    application_id = models.CharField(max_length=25, unique=True, null=True, blank=True)  # Ensure uniqueness
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='change_requests')
    changes = models.JSONField(default=dict)  # Store the changes

    # Proposed new values for the editable fields from the Member model
    new_full_name = models.CharField(max_length=255, blank=True, null=True)
    new_father_name = models.CharField(max_length=255, blank=True, null=True)
    new_cnic = models.CharField(max_length=13, blank=True, null=True)
    new_dob = models.DateField(blank=True, null=True)
    new_gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True,
                                  null=True)
    new_nic_type = models.CharField(max_length=50, choices=[('cnic', 'CNIC'), ('nicop', 'NICOP')], blank=True,
                                    null=True)
    new_country_of_stay = CountryField(blank_label='Select Country', blank=True, null=True)
    new_present_address = models.TextField(blank=True, null=True)
    new_permanent_address = models.TextField(blank=True, null=True)
    new_dual_citizen = models.CharField(
        max_length=3,
        default='no',
        blank=True, null=True
    )
    new_other_citizenship = CountryField(blank=True, null=True)
    new_pri_mob = models.CharField(max_length=15, blank=True, null=True)
    new_sec_mob = models.CharField(max_length=15, blank=True, null=True)
    new_designation = models.CharField(max_length=100, blank=True, null=True)
    new_business_name = models.CharField(max_length=255, blank=True, null=True)
    new_business_address = models.TextField(blank=True, null=True)
    new_tehsil = models.ForeignKey('Tehsil', on_delete=models.SET_NULL, null=True, blank=True)
    new_district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    new_pri_land = models.CharField(max_length=15, blank=True, null=True)
    new_sec_land = models.CharField(max_length=15, blank=True, null=True)
    new_employee_number = models.CharField(max_length=20, blank=True, null=True)

    # Request status fields
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    submission_date = models.DateTimeField(default=timezone.now)
    admin_reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, default=None)  # Link to Fee directly
    def __str__(self):
        return f"Change Request for {self.member.full_name} on {self.submission_date}"

    def apply_changes(self):
        """Apply changes to the original Member model when approved, and track changes."""
        member = self.member
        previous_values = {}

        # Apply changes based on the edited values
        if self.changes:
            for field, change in self.changes.items():
                new_value = change['new']  # Get the edited value from the changes
                old_value = getattr(member, field, None)  # Get the current value of the field

                if new_value is not None and new_value != old_value:
                    previous_values[field] = old_value  # Store the old value for tracking
                    setattr(member, field, new_value)  # Update the member's field

        # Save the updated member information
        member.save()

        # Log the previous values of changed fields
        if previous_values:
            self.changes = previous_values  # Update changes with previous values
            self.save()
