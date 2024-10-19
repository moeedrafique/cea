from .models import Member


def member_name(request):
    if request.user.is_authenticated:
        # Get the authenticated user
        member = Member.objects.get(user=request.user)
        return {'member': member}  # Change to member.first_name or other fields as needed
    return {}