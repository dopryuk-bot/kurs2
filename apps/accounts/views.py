from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.accounts.forms import (
    EmailLoginForm,
    StarostaCreateForm,
    StarostaUpdateForm,
    TeacherCreateForm,
    TeacherUpdateForm,
)
from apps.accounts.models import Role, User
from core.mixins import AdminRequiredMixin


class LoginView(View):
    template_name = 'accounts/login.html'
    form_class = EmailLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, _(f'Ласкаво просимо, {user.get_short_name()}!'))
            next_url = request.GET.get('next')
            return redirect(next_url or user.get_dashboard_url())
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, _('Ви вийшли з системи.'))
        return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


# ─── Teacher management ───────────────────────────────────────────────────────

class TeacherListView(AdminRequiredMixin, ListView):
    template_name = 'accounts/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 25

    def get_queryset(self):
        qs = (
            User.objects.filter(role=Role.TEACHER)
            .select_related('teacher_profile')
            .order_by('full_name')
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q)
                | Q(email__icontains=q)
                | Q(teacher_profile__department__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['total_count'] = User.objects.filter(role=Role.TEACHER).count()
        return ctx


class TeacherCreateView(AdminRequiredMixin, CreateView):
    form_class = TeacherCreateForm
    template_name = 'accounts/teacher_form.html'
    success_url = reverse_lazy('accounts:teacher_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Новий викладач')}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Викладача успішно створено.'))
        return response


class TeacherUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = TeacherUpdateForm
    template_name = 'accounts/teacher_form.html'
    success_url = reverse_lazy('accounts:teacher_list')

    def get_queryset(self):
        return User.objects.filter(role=Role.TEACHER)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування викладача')}

    def form_valid(self, form):
        messages.success(self.request, _('Дані викладача оновлено.'))
        return super().form_valid(form)


class TeacherDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/teacher_confirm_delete.html'
    success_url = reverse_lazy('accounts:teacher_list')

    def get_queryset(self):
        return User.objects.filter(role=Role.TEACHER)

    def form_valid(self, form):
        messages.success(self.request, _('Викладача видалено.'))
        return super().form_valid(form)


# ─── Starosta management ──────────────────────────────────────────────────────

class StarostaListView(AdminRequiredMixin, ListView):
    template_name = 'accounts/starosta_list.html'
    context_object_name = 'starostas'
    paginate_by = 25

    def get_queryset(self):
        qs = (
            User.objects.filter(role=Role.STAROSTA)
            .select_related('starosta_profile__group')
            .order_by('full_name')
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(full_name__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['total_count'] = User.objects.filter(role=Role.STAROSTA).count()
        return ctx


class StarostaCreateView(AdminRequiredMixin, CreateView):
    form_class = StarostaCreateForm
    template_name = 'accounts/starosta_form.html'
    success_url = reverse_lazy('accounts:starosta_list')

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Новий(а) Староста')}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Старосту успішно створено.'))
        return response


class StarostaUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = StarostaUpdateForm
    template_name = 'accounts/starosta_form.html'
    success_url = reverse_lazy('accounts:starosta_list')

    def get_queryset(self):
        return User.objects.filter(role=Role.STAROSTA)

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'title': _('Редагування старости')}

    def form_valid(self, form):
        messages.success(self.request, _('Дані старости оновлено.'))
        return super().form_valid(form)


class StarostaDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/starosta_confirm_delete.html'
    success_url = reverse_lazy('accounts:starosta_list')

    def get_queryset(self):
        return User.objects.filter(role=Role.STAROSTA)

    def form_valid(self, form):
        messages.success(self.request, _('Старосту видалено.'))
        return super().form_valid(form)
