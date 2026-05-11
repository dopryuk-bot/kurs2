from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Base mixin that restricts access to specific roles.
    Subclass it and set `allowed_roles` to a list of role strings.
    Raises 403 (not redirect) when authenticated user lacks the required role.
    """

    allowed_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']


class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['teacher', 'admin']


class StarostaRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['starosta', 'admin']


class AnyRoleRequiredMixin(RoleRequiredMixin):
    """Allows any authenticated user with an assigned role (all three roles)."""
    allowed_roles = ['admin', 'teacher', 'starosta']
