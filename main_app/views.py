import os
import random
import string
import traceback
from datetime import timedelta, date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
import pdfkit
# Create your views here.
from django.template.loader import get_template
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django_countries import countries

from .decorator import anonymous_required
from .forms import *
from .models import *

@login_required(login_url='login')
def dash(request):
    city = District.objects.all()
    tehsil = Tehsil.objects.all()
    # Get today's date and calculate first day of current month and previous month
    today = date.today()
    first_day_of_current_month = today.replace(day=1)
    first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)

    # Count active, pending, and suspended members for the current month
    active_members_count = Member.objects.filter(status='active', joined_at__gte=first_day_of_current_month).count()
    pending_members_count = Member.objects.filter(status='pending', created_at__gte=first_day_of_current_month).count()
    suspended_members_count = Member.objects.filter(status='suspended',
                                                    joined_at__gte=first_day_of_current_month).count()

    # Count active, pending, and suspended members for the previous month
    prev_active_members_count = Member.objects.filter(status='active', joined_at__gte=first_day_of_previous_month,
                                                      joined_at__lt=first_day_of_current_month).count()
    prev_pending_members_count = Member.objects.filter(status='pending', created_at__gte=first_day_of_previous_month,
                                                       joined_at__lt=first_day_of_current_month).count()
    prev_suspended_members_count = Member.objects.filter(status='suspended', joined_at__gte=first_day_of_previous_month,
                                                         joined_at__lt=first_day_of_current_month).count()

    # Calculate percentage changes
    def calculate_percentage_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    active_percentage_change = calculate_percentage_change(active_members_count, prev_active_members_count)
    pending_percentage_change = calculate_percentage_change(pending_members_count, prev_pending_members_count)
    suspended_percentage_change = calculate_percentage_change(suspended_members_count, prev_suspended_members_count)
    members = Member.objects.all()
    context = {
        'active_members_count': active_members_count,
        'pending_members_count': pending_members_count,
        'suspended_members_count': suspended_members_count,
        'active_percentage_change': active_percentage_change,
        'pending_percentage_change': pending_percentage_change,
        'suspended_percentage_change': suspended_percentage_change,
        'today': today,
        'members': members,
        'tehsil': tehsil,
        'city': city,
        'countries': countries,
    }
    return render(request, 'dashboard.html', context)

def members(request):
    members = Member.objects.all()
    context = {'members': members}
    return render(request, 'members.html', context)



from datetime import datetime
from django.utils import timezone


def generate_application_id(fee_type):
    # Get the current year
    current_year = datetime.now().year

    # Get the prefix based on the fee type
    prefix = 'PK-CEAAJK'

    # Get the code for the selected fee type
    fee_code = FEE_TYPE_CODES.get(fee_type, 'UNKNOWN')  # Default to 'UNKNOWN' if fee_type is not found

    # Check if there are any existing entries in the Fee model
    last_fee = Fee.objects.filter(fee_type=fee_type, is_approved=True).last()

    # If no previous IDs exist, start from 0
    last_number = 0

    # Check if there's a previous application_id and if it's valid
    if last_fee and last_fee.application_id:
        try:
            last_number_part = last_fee.application_id.split('-')[-1]
            if last_number_part.isdigit():
                last_number = int(last_number_part)
            else:
                print(f"Warning: Invalid application_id format '{last_fee.application_id}'")
        except ValueError as e:
            print(f"Error processing application_id: {e}")

    # Increment to generate a new application ID
    new_number = last_number + 1

    # Format the new application ID
    new_application_id = f"{prefix}-{fee_code}-{current_year}-{new_number:04d}"

    return new_application_id


def calculate_member_till(joined_date):
    # Convert to naive datetime for comparison if needed
    if timezone.is_aware(joined_date):
        joined_date = timezone.make_naive(joined_date)

    current_year = joined_date.year

    # Define the comparison date as naive datetime
    cutoff_date = datetime(current_year, 9, 30)

    if current_year % 2 == 0:
        # If it's an even year
        if joined_date <= cutoff_date:
            member_till = datetime(current_year + 2, 10, 31)
        else:
            member_till = datetime(current_year + 2, 10, 31)
    else:
        # If it's an odd year
        member_till = datetime(current_year + 1, 10, 31)

    # Return the calculated member till date as a naive datetime
    return member_till


@anonymous_required(redirect_url='home')  # Redirect logged-in users to 'home' page
def signup_view(request):
    city = District.objects.all()
    tehsil = Tehsil.objects.all()
    payment_details = Payment.objects.all()

    SIGNUP_FEE = 45000.00

    if request.method == 'POST':
        member_form = MemberForm(request.POST, request.FILES)
        fee_renewal_form = FeeRenewalForm(request.POST)

        if member_form.is_valid() and fee_renewal_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the member
                    member = member_form.save()

                    # Prepare the fee renewal but don't save it yet
                    fee_renewal = fee_renewal_form.save(commit=False)
                    fee_renewal.fee_type = 'new registration'
                    fee_renewal.member = member  # Link the fee renewal to the member

                    # Generate the application ID after setting fee_renewal.fee_type
                    application_id = generate_application_id(fee_renewal.fee_type)
                    member.application_id = application_id
                    member.save()

                    # Set total amount and calculate amount remaining
                    total_amount = SIGNUP_FEE  # Total fee
                    amount_paid = float(request.POST.get('amount_paid', 0))  # Get the amount paid, default to 0
                    fee_renewal.amount_remaining = total_amount - amount_paid  # Calculate amount remaining

                    # Save the fee renewal
                    fee_renewal.save()

                # Check if it's an AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': "Your registration was successful!"})

                # Handle non-AJAX POST request
                messages.success(request, "Your registration was successful!")
                return redirect(reverse('success_url'))  # Replace with your success URL

            except Exception as e:
                error_message = f"Error occurred: {str(e)}\nTraceback:\n{traceback.format_exc()}"
                print(error_message)  # Print detailed error to console or log
                # Handle any exceptions that occur during the transaction
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)})
                else:
                    messages.error(request, f"An error occurred: {str(e)}")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Send errors in JSON format for AJAX
                errors = {}

                # Check for errors in member_form
                for field, error_list in member_form.errors.items():
                    if isinstance(error_list, list):
                        errors[field] = error_list
                    else:
                        errors[field] = [error_list]

                # Check for errors in fee_renewal_form
                for field, error_list in fee_renewal_form.errors.items():
                    if isinstance(error_list, list):
                        errors[field] = error_list
                    else:
                        errors[field] = [error_list]

                return JsonResponse({'success': False, 'errors': errors})
            else:
                # Add form errors to Django messages
                for field, error_list in member_form.errors.items():
                    for error in error_list:
                        messages.error(request, f"{field}: {error}")

                for field, error_list in fee_renewal_form.errors.items():
                    for error in error_list:
                        messages.error(request, f"{field}: {error}")

    else:
        member_form = MemberForm()
        fee_renewal_form = FeeRenewalForm()

    return render(
        request,
        'sign-up.html',
        {
            'member_form': member_form,
            'fee_renewal_form': fee_renewal_form,
            'city': city,
            'tehsil': tehsil,
            'countries': countries,
            'payment_details': payment_details
        }
    )

@anonymous_required(redirect_url='home')  # Redirect logged-in users to 'home' page
def signup_success(request):
    return render(request, 'signup_success.html')

User = get_user_model()


@anonymous_required(redirect_url='home')  # Redirect logged-in users to 'home' page
def login_view(request):
    if request.method == 'POST':
        currency_association_id = request.POST.get('currency_association_id')
        last_4_cnic_digits = request.POST.get('last_4_cnic_digits')

        # Authenticate using the custom backend
        user = authenticate(request, currency_association_id=currency_association_id,
                            last_4_cnic_digits=last_4_cnic_digits)

        if user is not None:
            try:
                # Check if the user has an associated Member record
                member = Member.objects.get(user=user)

                # Check if the member is approved and active
                if member.is_approved and member.status == 'active':
                    login(request, user)
                    return redirect('home')  # Redirect after successful login
                else:
                    # Handle case where the member is not approved or not active
                    error_message = 'Your account is not active or not approved by admin.'
                    return render(request, 'sign-in.html', {'error': error_message})

            except Member.DoesNotExist:
                # Handle case where no member record is found
                return render(request, 'sign-in.html', {'error': 'Member record not found.'})
        else:
            # Handle invalid credentials
            return render(request, 'sign-in.html', {'error': 'Invalid ID or CNIC'})

    return render(request, 'sign-in.html')

def logout_view(request):
    # Log the user out
    logout(request)

    # Redirect to the login page or home page after logout
    return redirect('login')  # Assuming 'login' is the name of your login view

def get_tehsils(request, district_id):
    tehsils = Tehsil.objects.filter(district_id=district_id)
    tehsil_list = [{"id": tehsil.id, "name": tehsil.name} for tehsil in tehsils]
    return JsonResponse({"tehsils": tehsil_list})

@login_required
def submit_fees(request):
    try:
        member = request.user.member  # Ensure the user has a member profile
    except Member.DoesNotExist:
        messages.error(request, "You must be a member to submit fees.")
        return redirect('profile')  # Redirect to profile if not a member

    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.member = member  # Link fee to the logged-in member
            fee.save()

            messages.success(request, "Fees submitted successfully!")
            return redirect('profile')  # Redirect to profile after successful submission
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FeeForm()

    return render(request, 'submit_fees.html', {'form': form})



def generate_transaction_id(length=16):
    """Generate a random alphanumeric transaction ID of specified length."""
    characters = string.ascii_letters + string.digits  # Include letters and numbers
    return ''.join(random.choice(characters) for _ in range(length))

FEE_TYPE_CODES = {
    'new registration': 'NRG',
    'renewal': 'RNW',
    'change of information': 'ICG',
    'transfer of ownership': 'TOO',
    'transfer of ownership (DEATH OF ORIGINAL OWNER)': 'TOD',
}




@login_required
def renew_membership(request):
    # Define the renewal fee amount
    RENEWAL_FEE = 7000.00  # Example fee amount
    # Get the member associated with the logged-in user
    member = get_object_or_404(Member, user=request.user)
    payment_details = Payment.objects.all()
    city = District.objects.all()
    tehsil = Tehsil.objects.all()

    # Initialize the form (you can keep this if you still want to show it in the GET request)
    form = FeeRenewalForm(initial={'total_amount': RENEWAL_FEE})  # Set initial total amount

    # Handle POST request for fee renewal and change request
    if request.method == 'POST':
        form = FeeRenewalForm(request.POST)
        print(form)
        if form.is_valid():
            print(form.is_valid())
            try:
                with transaction.atomic():  # Start atomic transaction
                    # Handle fee renewal
                    fee = form.save(commit=False)
                    print(f"Fee object created: {fee}")  # Print the fee object for debugging
                    fee.member = member  # Link fee to the logged-in member
                    print(member, fee.member)
                    fee.fee_type = 'renewal'
                    fee.renewal_date = timezone.now()  # Set the renewal date to now
                    # Set total amount and calculate amount remaining
                    total_amount = RENEWAL_FEE  # Total fee
                    amount_paid = float(request.POST.get('amount_paid', 0))  # Get the amount paid, default to 0
                    fee.amount_remaining = total_amount - amount_paid  # Calculate amount remaining

                    # Generate transaction ID if submission method is 'cash'
                    if request.POST.get('submission_method') == 'cash':
                        fee.transaction_id = generate_transaction_id()  # Automatically generate transaction ID

                    fee.save()  # Save the fee record

                    member.member_till = calculate_member_till(member.joined_at)  # Calculate the new membership till date
                    member.save()

                    # Prepare change request data
                    changes = {}
                    new_full_name = request.POST.get('new_full_name', member.full_name)
                    if new_full_name and new_full_name != member.full_name:
                        changes['full_name'] = {
                            'previous': member.full_name,
                            'new': new_full_name
                        }
                    new_father_name = request.POST.get('new_father_name', member.father_name)
                    if new_father_name and new_father_name != member.father_name:
                        changes['father_name'] = {
                            'previous': member.father_name,
                            'new': new_father_name
                        }
                    new_cnic = request.POST.get('new_cnic', member.cnic)
                    if new_cnic and new_cnic != member.cnic:
                        changes['cnic'] = {
                            'previous': member.cnic,
                            'new': new_cnic
                        }
                    new_dob = request.POST.get('new_dob', member.dob)
                    if new_dob and new_dob != member.dob:
                        changes['dob'] = {
                            'previous': member.dob,
                            'new': new_dob
                        }
                    new_gender = request.POST.get('new_gender', member.gender)
                    if new_gender and new_gender != member.gender:
                        changes['gender'] = {
                            'previous': member.gender,
                            'new': new_gender
                        }
                    new_nic_type = request.POST.get('new_nic_type', member.nic_type)
                    if new_nic_type and new_nic_type != member.nic_type:
                        changes['nic_type'] = {
                            'previous': member.nic_type,
                            'new': new_nic_type
                        }
                    new_country_of_stay = request.POST.get('new_country_of_stay', member.country_of_stay)
                    if new_country_of_stay and new_country_of_stay != member.country_of_stay:
                        changes['country_of_stay'] = {
                            'previous': str(member.country_of_stay),  # Convert previous country to string
                            'new': str(new_country_of_stay)  # Convert new country to string
                        }

                    new_present_address = request.POST.get('new_present_address', member.present_address)
                    if new_present_address and new_present_address != member.present_address:
                        changes['present_address'] = {
                            'previous': member.present_address,
                            'new': new_present_address
                        }
                    new_permanent_address = request.POST.get('new_permanent_address', member.permanent_address)
                    if new_permanent_address and new_permanent_address != member.permanent_address:
                        changes['permanent_address'] = {
                            'previous': member.permanent_address,
                            'new': new_permanent_address
                        }
                    new_dual_citizen = request.POST.get('new_dual_citizen', member.dual_citizen)
                    print(new_dual_citizen)
                    if new_dual_citizen is not None and new_dual_citizen != member.dual_citizen:
                        changes['dual_citizen'] = {
                            'previous': member.dual_citizen,
                            'new': new_dual_citizen
                        }
                    new_other_citizenship = request.POST.get('new_other_citizenship', member.other_citizenship)
                    if new_other_citizenship and new_other_citizenship != member.other_citizenship:
                        changes['other_citizenship'] = {
                            'previous': member.other_citizenship,
                            'new': new_other_citizenship
                        }
                    new_pri_mob = request.POST.get('new_pri_mob', member.pri_mob)
                    if new_pri_mob and new_pri_mob != member.pri_mob:
                        changes['pri_mob'] = {
                            'previous': member.pri_mob,
                            'new': new_pri_mob
                        }
                    new_sec_mob = request.POST.get('new_sec_mob', member.sec_mob)
                    if new_sec_mob and new_sec_mob != member.sec_mob:
                        changes['sec_mob'] = {
                            'previous': member.sec_mob,
                            'new': new_sec_mob
                        }
                    new_designation = request.POST.get('new_designation', member.designation)
                    if new_designation and new_designation != member.designation:
                        changes['designation'] = {
                            'previous': member.designation,
                            'new': new_designation
                        }
                    new_business_name = request.POST.get('new_business_name', member.business_name)
                    if new_business_name and new_business_name != member.business_name:
                        changes['business_name'] = {
                            'previous': member.business_name,
                            'new': new_business_name
                        }
                    new_business_address = request.POST.get('new_business_address', member.business_address)
                    if new_business_address and new_business_address != member.business_address:
                        changes['business_address'] = {
                            'previous': member.business_address,
                            'new': new_business_address
                        }
                    # Initialize new_tehsil_obj and new_district_obj to None
                    new_tehsil_obj = None
                    new_district_obj = None

                    # Handle the new district change
                    # Handle the new district change
                    new_district_id = request.POST.get('new_district')
                    if new_district_id and new_district_id != str(member.district.id if member.district else None):
                        new_district_obj = get_object_or_404(District,
                                                             id=new_district_id)  # Get the district object by ID
                        changes['district'] = {
                            'previous': member.district.name if member.district else None,
                            'new': new_district_obj.name
                        }
                        member.district = new_district_obj  # Update the member's district

                    # Handle the new tehsil change
                    new_tehsil_id = request.POST.get('new_tehsil')
                    if new_tehsil_id and new_tehsil_id != str(member.tehsil.id if member.tehsil else None):
                        new_tehsil_obj = get_object_or_404(Tehsil, id=new_tehsil_id)  # Get the tehsil object by ID
                        changes['tehsil'] = {
                            'previous': member.tehsil.name if member.tehsil else None,
                            'new': new_tehsil_obj.name
                        }
                        member.tehsil = new_tehsil_obj  # Update the member's tehsil

                    print(f"District ID: {new_district_id}")
                    print(f"New District Object: {new_district_obj}")
                    new_pri_land = request.POST.get('new_pri_land', member.pri_land)
                    if new_pri_land and new_pri_land != member.pri_land:
                        changes['pri_land'] = {
                            'previous': member.pri_land,
                            'new': new_pri_land
                        }
                    new_sec_land = request.POST.get('new_sec_land', member.sec_land)
                    if new_sec_land and new_sec_land != member.sec_land:
                        changes['sec_land'] = {
                            'previous': member.sec_land,
                            'new': new_sec_land
                        }
                    new_employee_number = request.POST.get('new_employee_number', member.employee_number)
                    if new_employee_number and new_employee_number != member.employee_number:
                        changes['employee_number'] = {
                            'previous': member.employee_number,
                            'new': new_employee_number
                        }
                    print(changes)
                    # Save change request if there are any changes
                    change_request = MemberChangeRequest(
                        member=member,
                        fee=fee,
                        changes=changes  # Store the changes
                    )
                    print(change_request)
                    change_request.new_full_name = new_full_name
                    change_request.new_father_name = new_father_name
                    change_request.new_cnic = new_cnic
                    change_request.new_dob = new_dob
                    change_request.new_gender = new_gender
                    change_request.new_nic_type = new_nic_type
                    change_request.new_country_of_stay = new_country_of_stay
                    change_request.new_present_address = new_present_address
                    change_request.new_permanent_address = new_permanent_address
                    change_request.new_dual_citizen = new_dual_citizen
                    change_request.new_other_citizenship = new_other_citizenship
                    change_request.new_pri_mob = new_pri_mob
                    change_request.new_sec_mob = new_sec_mob
                    change_request.new_designation = new_designation
                    change_request.new_business_name = new_business_name
                    change_request.new_business_address = new_business_address
                    # Only assign new_tehsil and new_district if they were updated
                    if new_tehsil_obj:
                        change_request.new_tehsil = new_tehsil_obj
                    else:
                        change_request.new_tehsil = member.tehsil  # Keep current tehsil if no new tehsil is set
                    if new_district_obj:
                        change_request.new_district = new_district_obj
                    else:
                        change_request.new_district = member.district  # Keep current tehsil if no new tehsil is set
                    change_request.new_pri_land = new_pri_land
                    change_request.new_sec_land = new_sec_land
                    change_request.new_employee_number = new_employee_number

                    # Generate the application ID based on fee type
                    application_id = generate_application_id(fee.fee_type)
                    change_request.application_id = application_id
                    change_request.save()

                    return JsonResponse({
                        'status': 'success',
                        'message': f"Application Submitted Successfully! Application ID: {application_id}"
                    })
            except IntegrityError:
                # Handle unique constraint violation
                return JsonResponse({
                    'status': 'error',
                    'message': "An application with your ID already exists."
                })
            except Exception as e:
                error_message = f"Error occurred: {str(e)}\nTraceback:\n{traceback.format_exc()}"
                print(error_message)  # Print detailed error to console or log
                return JsonResponse({
                    'status': 'error',
                    'message': f"An error occurred: {str(e)}"
                })

                # Optionally log the error or handle it accordingly
        else:
            return JsonResponse({
                'status': 'error',
                'message': "Form submission failed. Please check the input fields."
            })
    # Render the template with the form
    return render(request, 'renew_membership.html', {
        'form': form,
        'payment_details': payment_details,
        'city': city,
        'tehsil': tehsil,
        'countries': countries
    })

@user_passes_test(lambda u: u.is_staff)  # Ensure only admins can access
def pending_requests(request):
    # Query all unapproved/unrejected change requests
    pending_requests = MemberChangeRequest.objects.filter(is_approved=False, is_rejected=False)

    return render(request, 'admin_pending_requests.html', {
        'pending_requests': pending_requests,
    })


@user_passes_test(lambda u: u.is_staff)  # Ensure only admins can access
def view_change_request(request, request_id):
    change_request = get_object_or_404(MemberChangeRequest, id=request_id)
    fee = get_object_or_404(Fee, member=change_request.member, fee_type="renewal")

    if request.method == 'POST':
        with transaction.atomic():
            payment_approved = fee.is_approved  # Track the state of payment approval
            changes_made = False  # Track if any changes are made

            # Check if changes exist or auto-approve the request
            if not change_request.changes:
                change_request.is_approved = True
                change_request.admin_reviewed_at = timezone.now()
                messages.success(request, 'Change request automatically approved as there were no changes.')
                change_request.save()  # Save the automatic approval

            # Handle change request approval or rejection
            if 'approve_change_request' in request.POST:
                change_request.is_approved = True
                change_request.admin_reviewed_at = timezone.now()

                # Update changes with admin edits
                if change_request.changes:
                    for field, values in change_request.changes.items():
                        new_value = request.POST.get(f'changes[{field}]')
                        print(new_value)
                        if new_value:
                            # Assuming change_request.changes is a dictionary
                            change_request.changes[field]['new'] = new_value
                            print(change_request.changes[field]['new'])
                change_request.save()

            elif 'reject_change_request' in request.POST:
                reason = request.POST.get('rejection_reason', '')
                change_request.is_rejected = True
                change_request.rejection_reason = reason
                change_request.admin_reviewed_at = timezone.now()
                change_request.save()
                messages.success(request, 'Change request rejected successfully.')
                return redirect('pending_requests')

            # Process payment approval or rejection
            if 'approve_payment' in request.POST:
                fee.is_approved = True
                payment_approved = True
                fee.save()
            elif 'reject_payment' in request.POST:
                fee.is_approved = False
                fee.save()
                messages.success(request, 'Payment rejected successfully.')
                return redirect('pending_requests')


            # Apply changes only if both are approved, whether changes were made or not
            if change_request.is_approved and payment_approved:
                change_request.apply_changes()  # Apply changes to the member model
                # Calculate and update member till date
                member = change_request.member  # Get the member instance
                member.member_till = calculate_member_till(timezone.now())  # Use the reusable function
                member.save()  # Save the updated member instance
                messages.success(request, 'Changes have been applied successfully.')
                return redirect('home')
            else:
                messages.info(request, 'No changes were made to apply, but the request has been approved.')

            # Save both models
            change_request.save()
            fee.save()

    return render(request, 'admin_view_request.html', {
        'change_request': change_request,
        'member': change_request.member,
        'changes': change_request.changes,
        'fee': fee,
    })


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
@login_required
def view_member(request, member_id):
    try:
        # Retrieve the member by their ID
        member = get_object_or_404(Member, id=member_id)
        city = District.objects.all()
        tehsil = Tehsil.objects.all()
        fee = Fee.objects.filter(fee_type="new registration", member=member).first()
        print(fee)
        # Check if the logged-in user has permission to view or edit the member
        if not request.user.is_staff and member.user != request.user:
            raise PermissionDenied("You do not have permission to view or edit this member's details.")

        if request.method == 'POST':
            form = MemberDetailForm(request.POST, instance=member)  # Bind the form to the existing member instance
            if form.is_valid():
                form.save()  # This will save changes to the existing member, not create a new one.
                # Handle member and payment approval toggles
                member_approved = request.POST.get('approve_member') == 'on'
                payment_approved = request.POST.get('approve_payment') == 'on'

                # Update member approval status
                if member_approved:
                    member.is_approved = True
                else:
                    member.is_approved = False

                member.save()

                # Update payment approval status if fee exists
                if fee:
                    if payment_approved:
                        fee.is_approved = True
                    else:
                        fee.is_approved = False

                    fee.save()

                # Set status to 'active' if both approved, else 'pending' or 'suspended'
                if member_approved and payment_approved:
                    member.status = 'active'
                elif not member_approved and not payment_approved:
                    member.status = 'suspended'
                else:
                    member.status = 'pending'

                member.save()

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Member updated successfully!'})

                # Redirect to the same page after successful update
                return redirect('member_dashboard')
            else:
                # Return errors in JSON format for AJAX request
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': form.errors})

                # If form is invalid, display errors in the template
                return render(request, 'member_detail.html',{'form': form, 'fee':fee, 'member': member, 'city': city, 'tehsil': tehsil, 'countries': countries})

        else:
            form = MemberDetailForm(instance=member)  # Prepopulate the form with the existing member's data

    except Member.DoesNotExist:
        raise Http404("Member not found.")
    except PermissionDenied as e:
        return render(request, 'errors/403.html', {'message': str(e)})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return render(request, 'errors/500.html', {'message': 'An unexpected error occurred.'})

    return render(request, 'member_detail.html',
                  {'form': form, 'fee':fee, 'member': member, 'city': city, 'tehsil': tehsil, 'countries': countries})



@csrf_exempt
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_member_status(request, member_id):
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        fee = Fee.objects.filter(fee_type="new registration", member=member).first()

        # Check if payment is approved and include that in logic
        payment_approved = fee.is_approved if fee else False

        # Toggle status between 'active' and 'suspended', and handle approval logic
        if member.status == 'active':
            member.status = 'suspended'
            message = "Member suspended successfully."
        else:
            if not member.is_approved or not payment_approved:
                return JsonResponse({'error': 'Member or payment is not approved.'}, status=400)

            member.status = 'active'
            member.joined_at = timezone.now()  # Set the join date to the current time if not set
            member.member_till = calculate_member_till(member.joined_at)  # Calculate the new membership till date
            message = "Member activated successfully and membership updated."

        member.save()

        return JsonResponse({'success': True, 'status': member.status, 'message': message,
                             'member_till': member.member_till.strftime('%Y-%m-%d')})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def delete_member(request, member_id):
    if request.method == 'POST':
        member = get_object_or_404(Member, id=member_id)
        member.delete()
        return JsonResponse({'message': 'Member has been deleted successfully.'})
    return JsonResponse({'message': 'Invalid request.'}, status=400)


def tehsils_map(request):
    tehsils = Tehsil.objects.all()
    data = []
    for tehsil in tehsils:
        # Count the number of members in the current Tehsil
        member_count = Member.objects.filter(status='active', tehsil=tehsil).count()

        if tehsil.latitude and tehsil.longitude and member_count > 0:  # Check if members > 0
            data.append({
                'name': tehsil.name,
                'district': tehsil.district.name,
                'latitude': float(tehsil.latitude),
                'longitude': float(tehsil.longitude),
                'member_count': member_count,  # Add member count to the data
            })
    return JsonResponse(data, safe=False)


def generate_receipt_view(request, order_id):
    # Get the Member object
    member = get_object_or_404(Member, id=order_id)

    # Check if a MemberChangeRequest exists for the member
    change_request = MemberChangeRequest.objects.filter(member=member).first()
    if not change_request:
        return HttpResponse("Cannot generate receipt. No MemberChangeRequest found for this member.", status=400)

    # Check if the change request is approved
    if not change_request.is_approved:
        return HttpResponse("Cannot generate receipt. Member change request is not approved.", status=400)

    # Get the associated Fee for the member (handling the case where Fee doesn't exist)
    fee = Fee.objects.filter(member=member).first()
    if not fee or not fee.is_approved:
        return HttpResponse("Cannot generate receipt. Fee is not approved or does not exist.", status=400)
    # Prepare the context
    context = {
        'member': member,
        'application_id': change_request.application_id,
        'submission_date': change_request.submission_date,
        'fee': fee,
    #     'customer': customer,
    #     'car': car,
    #     'car_detail': car_detail,  # Single instance
    #     'company': company,
    #     'payment': payment,  # Single instance
    #     'duration': duration,  # Duration in days
    }

    # The name of your PDF file
    filename = '{}.pdf'.format(member.id)

    # HTML FIle to be converted to PDF - inside your Django directory
    template = get_template('pdf.html')

    # Render the HTML
    html = template.render(context)

    # Options - Very Important [Don't forget this]
    options = {
        'encoding': 'UTF-8',
        'javascript-delay': '10',  # Optional
        'enable-local-file-access': None,  # To be able to access CSS
        'page-size': 'A4',
        'orientation': 'portrait',
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
    }
    # Javascript delay is optional

    # Remember that location to wkhtmltopdf
    # For windows os
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

    # For linux
    # config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

    # IF you have CSS to add to template
    css1 = os.path.join(settings.CSS_LOCATION, 'libraries', 'assets', 'css', 'style.css')
    # css2 = os.path.join(settings.CSS_LOCATION, 'assets', 'css', 'dashboard.css')

    # Create the file
    file_content = pdfkit.from_string(html, False, configuration=config, options=options)

    # Create the HTTP Response
    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename = {}'.format(filename)

    # Return
    return response



def generate_member_detail(request, order_id):
    # Get the Member object
    member = get_object_or_404(Member, id=order_id)


    # Check if the change request is approved
    if not member.is_approved:
        return HttpResponse("Cannot generate receipt. Member is not approved.", status=400)

    # Get the associated Fee for the member (handling the case where Fee doesn't exist)
    fee = Fee.objects.filter(fee_type="new registration", member=member).first()
    if not fee or not fee.is_approved:
        return HttpResponse("Cannot generate receipt. Fee is not approved or does not exist.", status=400)
    # Prepare the context
    context = {
        'member': member,
        'application_id': member.application_id,
        'submission_date': member.created_at,
        'fee': fee,
    #     'customer': customer,
    #     'car': car,
    #     'car_detail': car_detail,  # Single instance
    #     'company': company,
    #     'payment': payment,  # Single instance
    #     'duration': duration,  # Duration in days
    }

    # The name of your PDF file
    filename = '{}.pdf'.format(member.id)

    # HTML FIle to be converted to PDF - inside your Django directory
    template = get_template('pdf.html')

    # Render the HTML
    html = template.render(context)

    # Options - Very Important [Don't forget this]
    options = {
        'encoding': 'UTF-8',
        'javascript-delay': '10',  # Optional
        'enable-local-file-access': None,  # To be able to access CSS
        'page-size': 'A4',
        'orientation': 'portrait',
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
    }
    # Javascript delay is optional

    # Remember that location to wkhtmltopdf
    # For windows os
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

    # For linux
    # config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

    # IF you have CSS to add to template
    css1 = os.path.join(settings.CSS_LOCATION, 'libraries', 'assets', 'css', 'style.css')
    # css2 = os.path.join(settings.CSS_LOCATION, 'assets', 'css', 'dashboard.css')

    # Create the file
    file_content = pdfkit.from_string(html, False, configuration=config, options=options)

    # Create the HTTP Response
    response = HttpResponse(file_content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename = {}'.format(filename)

    # Return
    return response