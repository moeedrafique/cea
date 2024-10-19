from django.contrib.auth.backends import BaseBackend
from .models import User, Member

class CustomBackend(BaseBackend):
    def authenticate(self, request, currency_association_id=None, last_4_cnic_digits=None):
        try:
            # Fetch user based on currency_association_id
            user = User.objects.get(currency_association_id=currency_association_id)
            # Get the related member
            member = Member.objects.get(user=user)
            # Check if the last 4 digits of the CNIC match
            if member.cnic and member.cnic.endswith(last_4_cnic_digits):
                return user
        except (User.DoesNotExist, Member.DoesNotExist):
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None