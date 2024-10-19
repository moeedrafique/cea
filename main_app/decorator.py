from django.shortcuts import redirect
from functools import wraps

def anonymous_required(redirect_url='home'):
    """
    Custom decorator to prevent logged-in users from accessing the view.
    If the user is logged in, they will be redirected to the specified URL.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(redirect_url)  # Redirect logged-in users
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
