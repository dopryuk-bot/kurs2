from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, DetailView, FormView, ListView, UpdateView,
)

from apps.groups import services
from apps.groups.forms import BulkStudentForm, GroupForm, StudentForm
from apps.groups.models import Group, Student
from core.mixins import AdminRequiredMixin


# ─── Group CRUD ───────────────────────────────────────────────────────────────

class GroupListView(AdminRequiredMixin, ListView):
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'
    paginate_by = 25

    def get_queryset(self):
        qs = Group.objects.annotate(
            active_student_count=Count('students', filter=Q(students__is_active=True)),
        ).prefetch_related('starostas__user').order_by('course', 'name')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)

        course = self.request.GET.get('course', '')
        if course.isdigit():
            qs = qs.filter(course=int(course))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['course_filter'] = self.request.GET.get('course', '')
        ctx['courses'] = sorted(Group.objects.values_list('course', flat=True).distinct())
        ctx['total_count'] = Group.objects.count()
        return ctx


class GroupCreateView(AdminRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'
    success_url = reverse_lazy('groups:list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Нова група'), 'action': 'create'}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Групу «%(name)s» успішно створено.') % {'name': form.instance.name})
        return response


class GroupDetailView(AdminRequiredMixin, DetailView):
    model = Group
    template_name = 'groups/group_detail.html'
    context_object_name = 'group'

    def get_queryset(self):
        return Group.objects.prefetch_related('students', 'starostas__user')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        group = self.object
        ctx['active_students'] = group.students.filter(is_active=True).order_by('full_name')
        ctx['inactive_students'] = group.students.filter(is_active=False).order_by('full_name')
        ctx['starostas'] = group.starostas.select_related('user').all()
        ctx['active_count'] = group.students.filter(is_active=True).count()
        ctx['total_count'] = group.students.count()
        return ctx


class GroupUpdateView(AdminRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'groups/group_form.html'

    def get_success_url(self):
        return reverse('groups:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування групи'), 'action': 'edit'}

    def form_valid(self, form):
        messages.success(self.request, _('Групу оновлено.'))
        return super().form_valid(form)


class GroupDeleteView(AdminRequiredMixin, DeleteView):
    model = Group
    template_name = 'groups/group_confirm_delete.html'
    success_url = reverse_lazy('groups:list')

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, _('Групу «%(name)s» видалено.') % {'name': name})
        return response


# ─── Student management ───────────────────────────────────────────────────────

class StudentCreateView(AdminRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'groups/student_form.html'

    def get_group(self):
        return get_object_or_404(Group, pk=self.kwargs['group_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['group'] = self.get_group()
        ctx['title'] = _('Додати студента')
        return ctx

    def form_valid(self, form):
        form.instance.group = self.get_group()
        messages.success(self.request, _('Студента додано.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('groups:detail', kwargs={'pk': self.kwargs['group_pk']})


class StudentUpdateView(AdminRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'groups/student_form.html'
    pk_url_kwarg = 'student_pk'

    def get_group(self):
        return get_object_or_404(Group, pk=self.kwargs['group_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['group'] = self.get_group()
        ctx['title'] = _('Редагування студента')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Дані студента оновлено.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('groups:detail', kwargs={'pk': self.kwargs['group_pk']})


class StudentDeleteView(AdminRequiredMixin, DeleteView):
    model = Student
    template_name = 'groups/student_confirm_delete.html'
    pk_url_kwarg = 'student_pk'

    def get_group(self):
        return get_object_or_404(Group, pk=self.kwargs['group_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['group'] = self.get_group()
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Студента видалено.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('groups:detail', kwargs={'pk': self.kwargs['group_pk']})


class BulkStudentCreateView(AdminRequiredMixin, FormView):
    form_class = BulkStudentForm
    template_name = 'groups/bulk_student_form.html'

    def get_group(self):
        return get_object_or_404(Group, pk=self.kwargs['group_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['group'] = self.get_group()
        return ctx

    def form_valid(self, form):
        group = self.get_group()
        names = form.get_names()
        if not names:
            messages.warning(self.request, _('Список студентів порожній.'))
            return self.form_invalid(form)
        created, skipped = services.bulk_create_students(group, names)
        if created:
            messages.success(self.request, _(f'Додано {created} студентів.'))
        if skipped:
            preview = ', '.join(skipped[:5])
            if len(skipped) > 5:
                preview += f' та ще {len(skipped) - 5}...'
            messages.warning(self.request, _(f'Пропущено {len(skipped)} (вже існують): {preview}'))
        return redirect(reverse('groups:detail', kwargs={'pk': group.pk}))
