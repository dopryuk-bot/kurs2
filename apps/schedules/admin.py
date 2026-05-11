from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.schedules.constants import LESSON_TIMES
from apps.schedules.models import Schedule, Semester, Subject, WeekType, LessonType


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short')
    search_fields = ('name',)

    @admin.display(description=_('Опис'))
    def description_short(self, obj):
        return obj.description[:80] + '…' if len(obj.description) > 80 else obj.description


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'first_study_week_date', 'active_badge')
    list_filter = ('is_active',)
    search_fields = ('name',)
    actions = ['activate_semester']

    @admin.display(description=_('Статус'), boolean=False)
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold">✓ Активний</span>')
        return format_html('<span style="color:#aaa">Неактивний</span>')

    @admin.action(description=_('Активувати обраний семестр'))
    def activate_semester(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, _('Оберіть рівно один семестр для активації.'), level='error')
            return
        from apps.schedules.services import activate_semester as svc_activate
        svc_activate(queryset.first())
        self.message_user(request, _('Семестр активовано.'))

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            Semester.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'group', 'weekday_display', 'lesson_number', 'time_display',
        'subject', 'teacher_short', 'lesson_type_badge', 'week_type', 'semester',
    )
    list_filter = ('semester', 'week_type', 'lesson_type', 'weekday', 'group')
    search_fields = ('subject__name', 'group__name', 'teacher__full_name')
    ordering = ('group__name', 'weekday', 'lesson_number', 'week_type')

    WEEKDAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

    @admin.display(description=_('День'))
    def weekday_display(self, obj):
        return self.WEEKDAY_LABELS[obj.weekday]

    @admin.display(description=_('Час'))
    def time_display(self, obj):
        return f'{obj.start_time.strftime("%H:%M")} – {obj.end_time.strftime("%H:%M")}'

    @admin.display(description=_('Викладач'))
    def teacher_short(self, obj):
        return obj.teacher.get_short_name()

    @admin.display(description=_('Тип'))
    def lesson_type_badge(self, obj):
        colors = {
            LessonType.LECTURE: '#0d6efd',
            LessonType.LAB: '#198754',
            LessonType.PRACTICE: '#fd7e14',
        }
        color = colors.get(obj.lesson_type, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 7px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_lesson_type_display()
        )
