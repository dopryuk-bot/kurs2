from django import forms
from django.utils.translation import gettext_lazy as _

from apps.groups.models import Group, Student, Subgroup


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'course')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '301-А'}),
            'course': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
        }
        labels = {
            'name': _('Назва групи'),
            'course': _('Курс'),
        }
        error_messages = {
            'name': {'unique': _('Група з такою назвою вже існує.')},
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('full_name', 'subgroup', 'is_active')
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Прізвище Ім\'я По-батькові',
            }),
            'subgroup': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'full_name': _('ПІБ студента'),
            'subgroup': _('Підгрупа (для лаб)'),
            'is_active': _('Активний'),
        }


class BulkStudentForm(forms.Form):
    students_text = forms.CharField(
        label=_('Список студентів'),
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 15,
            'placeholder': 'Іваненко Іван Іванович\nПетренко Петро Петрович\nСидоренко Марія Іванівна',
        }),
        help_text=_('Введіть ПІБ кожного студента з нового рядка.'),
    )

    def get_names(self) -> list[str]:
        lines = self.cleaned_data['students_text'].splitlines()
        return [line.strip() for line in lines if line.strip()]
