from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, StarostaProfile, TeacherProfile, User
from apps.groups.models import Group


class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••••••',
        }),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            self._user_cache = authenticate(self.request, email=email, password=password)
            if self._user_cache is None:
                raise forms.ValidationError(
                    _('Невірний email або пароль. Перевірте дані та спробуйте знову.')
                )
            if not self._user_cache.is_active:
                raise forms.ValidationError(
                    _('Цей акаунт деактивовано. Зверніться до адміністратора.')
                )
        return self.cleaned_data

    def get_user(self):
        return self._user_cache


# ─── Teacher management forms ─────────────────────────────────────────────────

class TeacherCreateForm(forms.ModelForm):
    password = forms.CharField(
        label=_('Пароль'),
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    department = forms.CharField(
        label=_('Кафедра'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Кафедра прикладної математики',
        }),
    )

    class Meta:
        model = User
        fields = ('email', 'full_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Іваненко Іван Іванович',
            }),
        }
        labels = {
            'email': _('Email'),
            'full_name': _('ПІБ'),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Role.TEACHER
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            TeacherProfile.objects.get_or_create(
                user=user,
                defaults={'department': self.cleaned_data.get('department', '')},
            )
        return user


class TeacherUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        label=_('Новий пароль'),
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text=_('Залиш пустим, якщо не потрібно змінювати.'),
    )
    department = forms.CharField(
        label=_('Кафедра'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('email', 'full_name', 'is_active')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': _('Email'),
            'full_name': _('ПІБ'),
            'is_active': _('Активний'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.fields['department'].initial = self.instance.teacher_profile.department
            except TeacherProfile.DoesNotExist:
                pass

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Цей email вже використовується.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
            profile, _ = TeacherProfile.objects.get_or_create(user=user)
            profile.department = self.cleaned_data.get('department', '')
            profile.save()
        return user


# ─── Starosta management forms ────────────────────────────────────────────────

class StarostaCreateForm(forms.ModelForm):
    password = forms.CharField(
        label=_('Пароль'),
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.order_by('course', 'name'),
        label=_('Група'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ('email', 'full_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Петренко Петро Петрович',
            }),
        }
        labels = {
            'email': _('Email'),
            'full_name': _('ПІБ'),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Користувач з таким email вже існує.'))
        return email

    def clean(self):
        cleaned = super().clean()
        group = cleaned.get('group')
        if group:
            count = StarostaProfile.objects.filter(group=group).count()
            if count >= 2:
                raise forms.ValidationError(
                    _('Група «%(group)s» вже має 2 старости. Максимально 2.'),
                    params={'group': group},
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Role.STAROSTA
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            StarostaProfile.objects.create(
                user=user,
                group=self.cleaned_data['group'],
            )
        return user


class StarostaUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        label=_('Новий пароль'),
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text=_('Залиш пустим, якщо не потрібно змінювати.'),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.order_by('course', 'name'),
        label=_('Група'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = User
        fields = ('email', 'full_name', 'is_active')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email': _('Email'),
            'full_name': _('ПІБ'),
            'is_active': _('Активний'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.fields['group'].initial = self.instance.starosta_profile.group
            except StarostaProfile.DoesNotExist:
                pass

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Цей email вже використовується.'))
        return email

    def clean(self):
        cleaned = super().clean()
        group = cleaned.get('group')
        if group and self.instance.pk:
            count = StarostaProfile.objects.filter(group=group).exclude(user=self.instance).count()
            if count >= 2:
                raise forms.ValidationError(
                    _('Група «%(group)s» вже має 2 старости.'),
                    params={'group': group},
                )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
            profile, _ = StarostaProfile.objects.get_or_create(user=user)
            profile.group = self.cleaned_data['group']
            profile.save()
        return user
