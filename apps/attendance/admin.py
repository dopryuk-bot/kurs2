from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'schedule', 'date', 'status', 'marked_by', 'updated_at')
    list_filter = ('status', 'date', 'schedule__group', 'schedule__subject')
    search_fields = ('student__full_name',)
    date_hierarchy = 'date'
    raw_id_fields = ('student', 'schedule', 'marked_by')
