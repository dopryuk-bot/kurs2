from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.groups.models import Group, Student


class StudentInline(admin.TabularInline):
    model = Student
    extra = 1
    fields = ('full_name', 'is_active')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'student_count', 'starosta_list', 'created_at')
    list_filter = ('course',)
    search_fields = ('name',)
    inlines = [StudentInline]

    @admin.display(description=_('Студентів'))
    def student_count(self, obj):
        return obj.students.filter(is_active=True).count()

    @admin.display(description=_('Старости'))
    def starosta_list(self, obj):
        starostas = obj.get_starostas()
        return ', '.join(s.user.full_name for s in starostas) or '—'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'is_active')
    list_filter = ('group', 'is_active')
    search_fields = ('full_name',)
