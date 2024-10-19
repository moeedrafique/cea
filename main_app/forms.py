from django import forms
from django_countries.widgets import CountrySelectWidget
from .models import *
from django_countries.fields import CountryField
from django_countries import countries


def generate_currency_association_id():
    # Get the last user with a currency_association_id starting with 'CEA-'
    last_user = User.objects.filter(currency_association_id__startswith='CEA-').order_by(
        'currency_association_id').last()

    if last_user:
        # Extract the numeric part and increment it
        last_id = last_user.currency_association_id
        numeric_part = int(last_id.split('-')[1])
        new_numeric_part = numeric_part + 1
        new_currency_association_id = f'CEA-{new_numeric_part:04d}'  # Keep 4 digits
    else:
        # Start at CEA-0200 if no users exist
        new_currency_association_id = 'CEA-0200'

    return new_currency_association_id


class MemberForm(forms.ModelForm):
    gender_choices = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    nic_type_choices = [
        ('cnic', 'CNIC'),
        ('nicop', 'NICOP'),
    ]
    yes_no_choices = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    gender = forms.ChoiceField(choices=gender_choices, widget=forms.RadioSelect, label="Gender")
    # dual_citizen = forms.ChoiceField(choices=yes_no_choices, widget=forms.RadioSelect, label="Dual Citizen", initial='no')
    nic_type = forms.ChoiceField(choices=nic_type_choices, label="Type of NIC")
    country_of_stay = CountryField(blank_label='Select Country').formfield(widget=CountrySelectWidget, initial='PK',
                                                                           label="Country of Stay")
    other_citizenship = CountryField(blank_label='Select Country').formfield(
        widget=CountrySelectWidget,
        label="Other Citizenship (if any)",
        required=False
    )

    class Meta:
        model = Member
        fields = [
            'full_name', 'father_name', 'cnic', 'dob', 'gender', 'nic_type',
            'country_of_stay', 'present_address', 'permanent_address',
            'dual_citizen', 'pri_mob', 'other_citizenship', 'sec_mob',
            'designation', 'business_name',
            'business_address', 'tehsil', 'district', 'pri_land',
            'employee_number', 'sec_land'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'present_address': forms.Textarea(attrs={'rows': 2}),
            'permanent_address': forms.Textarea(attrs={'rows': 2}),
            'business_address': forms.Textarea(attrs={'rows': 2}),
            'tehsil': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            # 'picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # Override the clean method to convert 'yes' and 'no' to boolean
    def clean_dual_citizen(self):
        data = self.cleaned_data['dual_citizen']
        if data == 'yes':
            return 'Yes'
        elif data == 'no':
            return 'No'
        return None
    def save(self, commit=True):
        # Generate the currency_association_id automatically
        currency_association_id = generate_currency_association_id()

        # Create a new User object with the generated ID
        user = User(
            currency_association_id=currency_association_id,
            username=currency_association_id,  # Set username to the generated ID
            role='member',  # Set default role or allow selection
        )

        if commit:
            user.save()  # Save the user

        member = super().save(commit=False)  # Create Member instance but don't save yet
        member.user = user  # Link the member to the created user

        if commit:
            member.save()  # Save the member

        return member

class MemberDetailForm(forms.ModelForm):
    gender_choices = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    nic_type_choices = [
        ('cnic', 'CNIC'),
        ('nicop', 'NICOP'),
    ]
    yes_no_choices = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    gender = forms.ChoiceField(choices=gender_choices, widget=forms.RadioSelect, label="Gender")
    # dual_citizen = forms.ChoiceField(choices=yes_no_choices, widget=forms.RadioSelect, label="Dual Citizen", initial='no')
    nic_type = forms.ChoiceField(choices=nic_type_choices, label="Type of NIC")
    country_of_stay = CountryField(blank_label='Select Country').formfield(widget=CountrySelectWidget, initial='PK',
                                                                           label="Country of Stay")
    other_citizenship = CountryField(blank_label='Select Country').formfield(
        widget=CountrySelectWidget,
        label="Other Citizenship (if any)",
        required=False
    )

    class Meta:
        model = Member
        fields = [
            'full_name', 'father_name', 'cnic', 'dob', 'gender', 'nic_type',
            'country_of_stay', 'present_address', 'permanent_address',
            'dual_citizen', 'pri_mob', 'other_citizenship', 'sec_mob',
            'designation', 'business_name',
            'business_address', 'tehsil', 'district', 'pri_land',
            'employee_number', 'sec_land'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'present_address': forms.Textarea(attrs={'rows': 2}),
            'permanent_address': forms.Textarea(attrs={'rows': 2}),
            'business_address': forms.Textarea(attrs={'rows': 2}),
            'tehsil': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            # 'picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['fee_type', 'submission_method', 'amount_submitted', 'amount_remaining', 'transaction_id', 'payment']

        widgets = {
            'fee_type': forms.Select(attrs={'class': 'form-control'}),
            'submission_method': forms.Select(attrs={'class': 'form-control', 'id': 'submission_method'}),
            'amount_submitted': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_remaining': forms.NumberInput(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account number'}),
        }


class FeeRenewalForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['submission_method', 'amount_submitted', 'transaction_id', 'payment']
        exclude = ['fee_type', 'amount_remaining', 'member']

    SUBMISSION_METHODS = [
        ('cash', 'By Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    submission_method = forms.ChoiceField(choices=SUBMISSION_METHODS, initial='cash')

    def __init__(self, *args, **kwargs):
        super(FeeRenewalForm, self).__init__(*args, **kwargs)
        # Set default submission_method to 'cash' if not already set
        if not self.initial.get('submission_method'):
            self.fields['submission_method'].initial = 'cash'

    def clean(self):
        cleaned_data = super().clean()
        amount_submitted = cleaned_data.get('amount_submitted')

        if amount_submitted < 0:
            self.add_error('amount_submitted', 'Amount submitted cannot be negative.')

        return cleaned_data

class MemberChangeRequestForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = '__all__' #  Include fields that can be changed