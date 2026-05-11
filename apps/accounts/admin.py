from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, StarostaProfile, TeacherProfile, User


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = _('Профіль викладача')
    fields = ('department',)


class StarostaProfileInline(admin.StackedInline):
    model = StarostaProfile
    can_delete = False
    verbose_name_plural = _('Профіль старости')
    fields = ('group',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('full_name',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Особисті дані'), {'fields': ('full_name', 'role')}),
        (_('Права'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Дати'), {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('created_at', 'last_login')

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == Role.TEACHER:
            return [TeacherProfileInline]
        if obj.role == Role.STAROSTA:
            return [StarostaProfileInline]
        return []
