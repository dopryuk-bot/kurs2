from apps.schedules.models import Semester


def user_role(request):
    """
    Injects user role into every template context.
    Allows role-based template rendering without template tags.
    """
    if not request.user.is_authenticated:
        return {}

    return {
        'user_role': request.user.role,
        'is_admin': request.user.is_admin,
        'is_teacher': request.user.is_teacher,
        'is_starosta': request.user.is_starosta,
    }


def active_semester(request):
    """
    Injects the active semester into every template context.
    Cached per-request via a simple attribute to avoid multiple DB queries.
    """
    if not request.user.is_authenticated:
        return {}

    if not hasattr(request, '_active_semester_cache'):
        request._active_semester_cache = Semester.objects.filter(is_active=True).first()

    return {'active_semester': request._active_semester_cache}
