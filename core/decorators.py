from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator for function-based views. Restricts access to specific roles.
    Usage: @role_required('admin', 'teacher')

    Raises PermissionDenied (403) rather than redirecting, to give a clear signal
    that the user is authenticated but unauthorized.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.conf import settings
                from django.shortcuts import redirect
                return redirect(f'{settings.LOGIN_URL}?next={request.path}')

            if request.user.role not in roles:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
