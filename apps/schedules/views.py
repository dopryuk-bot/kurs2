from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.schedules import services
from apps.schedules.forms import ScheduleFilterForm, ScheduleForm, SemesterForm, SubjectForm
from apps.schedules.models import Schedule, Semester, Subject, Weekday
from core.mixins import AdminRequiredMixin, StarostaRequiredMixin, TeacherRequiredMixin


# ─── Shared base ─────────────────────────────────────────────────────────────

class WeekNavigationMixin:
    """Parses ?week=YYYY-MM-DD from GET params and exposes navigation helpers."""

    def get_target_date(self) -> date:
        raw = self.request.GET.get('week', '')
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return date.today()


# ─── Starosta ─────────────────────────────────────────────────────────────────

class StarostaScheduleView(StarostaRequiredMixin, WeekNavigationMixin, TemplateView):
    template_name = 'schedules/week_calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = self.get_target_date()
        semester = services.get_active_semester()

        try:
            group = self.request.user.starosta_profile.group
        except Exception:
            ctx['error'] = _('Ви не закріплені за жодною групою.')
            return ctx

        if not semester:
            ctx['error'] = _('Активний семестр не знайдено.')
            return ctx

        week_type = semester.get_week_type(target)
        if not week_type:
            ctx['error'] = _('Обрана дата виходить за межі семестру.')
            return ctx

        schedules = services.get_schedules_for_group(group, semester, week_type)
        timetable_ctx = services.build_timetable_context(schedules, target, semester)

        return {**ctx, **timetable_ctx, 'group': group, 'view_mode': 'starosta'}


# ─── Teacher ──────────────────────────────────────────────────────────────────

class TeacherScheduleView(TeacherRequiredMixin, WeekNavigationMixin, TemplateView):
    template_name = 'schedules/week_calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = self.get_target_date()
        semester = services.get_active_semester()

        if not semester:
            ctx['error'] = _('Активний семестр не знайдено.')
            return ctx

        week_type = semester.get_week_type(target)
        if not week_type:
            ctx['error'] = _('Обрана дата виходить за межі семестру.')
            return ctx

        schedules = services.get_schedules_for_teacher(self.request.user, semester, week_type)
        timetable_ctx = services.build_timetable_context(schedules, target, semester)

        return {**ctx, **timetable_ctx, 'view_mode': 'teacher'}


# ─── Admin: Semester management ───────────────────────────────────────────────

class SemesterListView(AdminRequiredMixin, ListView):
    model = Semester
    template_name = 'schedules/admin/semester_list.html'
    context_object_name = 'semesters'
    queryset = Semester.objects.order_by('-start_date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_semester'] = services.get_active_semester()
        return ctx


class SemesterCreateView(AdminRequiredMixin, CreateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'schedules/admin/semester_form.html'
    success_url = reverse_lazy('schedules:semester_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Новий семестр')}

    def form_valid(self, form):
        messages.success(self.request, _('Семестр успішно створено.'))
        return super().form_valid(form)


class SemesterUpdateView(AdminRequiredMixin, UpdateView):
    model = Semester
    form_class = SemesterForm
    template_name = 'schedules/admin/semester_form.html'
    success_url = reverse_lazy('schedules:semester_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування семестру')}

    def form_valid(self, form):
        messages.success(self.request, _('Семестр успішно оновлено.'))
        return super().form_valid(form)


class SemesterDeleteView(AdminRequiredMixin, DeleteView):
    model = Semester
    template_name = 'schedules/admin/semester_confirm_delete.html'
    success_url = reverse_lazy('schedules:semester_list')

    def form_valid(self, form):
        messages.success(self.request, _('Семестр видалено.'))
        return super().form_valid(form)


# ─── Admin: Schedule management ───────────────────────────────────────────────

class ScheduleListView(AdminRequiredMixin, TemplateView):
    template_name = 'schedules/admin/schedule_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = services.get_active_semester()
        filter_form = ScheduleFilterForm(self.request.GET or None)
        filter_form.fields['semester'].initial = semester

        filters = {}
        if filter_form.is_valid():
            d = filter_form.cleaned_data
            filters = {k: v for k, v in d.items() if v not in (None, '')}
            if 'semester' not in filters and semester:
                filters['semester'] = semester
        elif semester:
            filters['semester'] = semester

        schedules = services.get_all_schedules(
            semester=filters.get('semester', semester),
            filters=filters,
        ) if filters.get('semester') or semester else []

        return {
            **ctx,
            'schedules': schedules,
            'filter_form': filter_form,
            'active_semester': semester,
        }


class ScheduleCreateView(AdminRequiredMixin, CreateView):
    model = Schedule
    form_class = ScheduleForm
    template_name = 'schedules/admin/schedule_form.html'
    success_url = reverse_lazy('schedules:schedule_list')

    def get_initial(self):
        initial = super().get_initial()
        semester = services.get_active_semester()
        if semester:
            initial['semester'] = semester
        return initial

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Нова пара')}

    def form_valid(self, form):
        messages.success(self.request, _('Пару успішно додано до розкладу.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Виправте помилки у формі.'))
        return super().form_invalid(form)


class ScheduleUpdateView(AdminRequiredMixin, UpdateView):
    model = Schedule
    form_class = ScheduleForm
    template_name = 'schedules/admin/schedule_form.html'
    success_url = reverse_lazy('schedules:schedule_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування пари')}

    def form_valid(self, form):
        messages.success(self.request, _('Пару успішно оновлено.'))
        return super().form_valid(form)


class ScheduleDeleteView(AdminRequiredMixin, DeleteView):
    model = Schedule
    template_name = 'schedules/admin/schedule_confirm_delete.html'
    success_url = reverse_lazy('schedules:schedule_list')

    def form_valid(self, form):
        messages.success(self.request, _('Пару видалено з розкладу.'))
        return super().form_valid(form)


# ─── Admin: Subject management ───────────────────────────────────────────────

class SubjectListView(AdminRequiredMixin, ListView):
    model = Subject
    template_name = 'schedules/admin/subject_list.html'
    context_object_name = 'subjects'
    paginate_by = 25

    def get_queryset(self):
        from django.db.models import Count
        qs = Subject.objects.annotate(schedules_count=Count('schedules')).order_by('name')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['total_count'] = Subject.objects.count()
        return ctx


class SubjectCreateView(AdminRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'schedules/admin/subject_form.html'
    success_url = reverse_lazy('schedules:subject_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Новий предмет')}

    def form_valid(self, form):
        messages.success(self.request, _('Предмет успішно створено.'))
        return super().form_valid(form)


class SubjectUpdateView(AdminRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'schedules/admin/subject_form.html'
    success_url = reverse_lazy('schedules:subject_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування предмету')}

    def form_valid(self, form):
        messages.success(self.request, _('Предмет оновлено.'))
        return super().form_valid(form)


class SubjectDeleteView(AdminRequiredMixin, DeleteView):
    model = Subject
    template_name = 'schedules/admin/subject_confirm_delete.html'
    success_url = reverse_lazy('schedules:subject_list')

    def form_valid(self, form):
        messages.success(self.request, _('Предмет видалено.'))
        return super().form_valid(form)


# ─── Admin: General (all-groups) timetable ───────────────────────────────────

class AdminGeneralTimetableView(AdminRequiredMixin, TemplateView):
    template_name = 'schedules/admin/general_timetable.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = services.get_active_semester()

        raw_wd = self.request.GET.get('weekday', '')
        try:
            weekday_filter = int(raw_wd)
            if weekday_filter not in range(6):
                weekday_filter = None
        except (ValueError, TypeError):
            weekday_filter = None

        if not semester:
            return {**ctx, 'error': _('Активний семестр не знайдено.'), 'weekday_choices': Weekday.choices}

        timetable = services.build_general_timetable(semester, weekday_filter=weekday_filter)
        return {
            **ctx,
            'semester': semester,
            'weekday_choices': Weekday.choices,
            'selected_weekday': weekday_filter,
            **timetable,
        }


# ─── Admin: Weekly timetable view ─────────────────────────────────────────────

class AdminTimetableView(AdminRequiredMixin, WeekNavigationMixin, TemplateView):
    template_name = 'schedules/week_calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        target = self.get_target_date()
        semester = services.get_active_semester()

        if not semester:
            return {**ctx, 'error': _('Активний семестр не знайдено.')}

        week_type = semester.get_week_type(target)
        group_id = self.request.GET.get('group')
        teacher_id = self.request.GET.get('teacher')

        filters = {'week_type': week_type} if week_type else {}
        if group_id:
            filters['group'] = group_id
        if teacher_id:
            filters['teacher'] = teacher_id

        schedules = services.get_all_schedules(semester=semester, filters=filters)
        timetable_ctx = services.build_timetable_context(schedules, target, semester)

        return {**ctx, **timetable_ctx, 'view_mode': 'admin'}
