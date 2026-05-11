from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role, User
from apps.groups.models import Group
from apps.schedules.constants import LESSON_CHOICES, LESSON_TIMES
from apps.schedules.models import (
    LessonType,
    Schedule,
    Semester,
    Subject,
    Subgroup,
    Weekday,
    WeekType,
)
from apps.schedules.services import get_conflicts, get_first_study_week_date, validate_semester_dates


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ('name', 'start_date', 'end_date')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'name': _('Назва семестру'),
            'start_date': _('Дата початку'),
            'end_date': _('Дата завершення'),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end:
            errors = validate_semester_dates(start, end)
            if errors:
                raise ValidationError(errors)
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.start_date:
            instance.first_study_week_date = get_first_study_week_date(instance.start_date)
        if commit:
            instance.save()
        return instance


class ScheduleForm(forms.ModelForm):
    # ── Text inputs — converted to model instances in clean_* ─────────────────
    subject = forms.CharField(
        label=_('Предмет'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Математичний аналіз',
            'autocomplete': 'off',
        }),
    )
    teacher = forms.CharField(
        label=_('Викладач (ПІБ)'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Іваненко Іван Іванович',
            'autocomplete': 'off',
        }),
    )
    group = forms.CharField(
        label=_('Група'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '301-А',
            'autocomplete': 'off',
        }),
    )
    subgroup = forms.ChoiceField(
        choices=[('', _('Без підгрупи'))] + list(Subgroup.choices),
        label=_('Підгрупа'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    create_parallel_subgroup = forms.BooleanField(
        label=_('Створити паралельну лабораторну для іншої підгрупи'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    parallel_teacher = forms.CharField(
        label=_('Викладач для паралельної підгрупи'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Іваненко Іван Іванович',
            'autocomplete': 'off',
        }),
    )
    parallel_lesson_number = forms.ChoiceField(
        choices=[('', _('Така сама пара'))] + LESSON_CHOICES,
        label=_('Пара для паралельної підгрупи'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    parallel_classroom = forms.CharField(
        label=_('Аудиторія для паралельної підгрупи'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '21',
            'autocomplete': 'off',
        }),
        help_text=_('Номер аудиторії для паралельної підгрупи (опціонально)'),
    )

    # ── Select fields ─────────────────────────────────────────────────────────
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.order_by('-start_date'),
        label=_('Семестр'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    lesson_type = forms.ChoiceField(
        choices=LessonType.choices,
        label=_('Тип заняття'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    weekday = forms.ChoiceField(
        choices=Weekday.choices,
        label=_('День тижня'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    lesson_number = forms.ChoiceField(
        choices=LESSON_CHOICES,
        label=_('Пара'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    week_type = forms.ChoiceField(
        choices=WeekType.choices,
        label=_('Тип тижня'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    classroom = forms.CharField(
        label=_('Аудиторія'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '21',
            'autocomplete': 'off',
        }),
        help_text=_('Номер або назва аудиторії'),
    )

    class Meta:
        model = Schedule
        # subject/teacher/group excluded — handled as CharFields above
        fields = ('semester', 'lesson_type', 'weekday', 'lesson_number', 'week_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill text fields when editing an existing schedule
        if self.instance and self.instance.pk:
            self.fields['subject'].initial = self.instance.subject.name
            self.fields['teacher'].initial = self.instance.teacher.full_name
            self.fields['group'].initial = self.instance.group.name
            self.fields['subgroup'].initial = self.instance.subgroup or ''
            self.fields['classroom'].initial = self.instance.classroom

    # ── Text → model instance converters ─────────────────────────────────────

    def clean_subject(self):
        name = self.cleaned_data['subject'].strip()
        subject, _ = Subject.objects.get_or_create(name=name)
        return subject

    def clean_teacher(self):
        name = self.cleaned_data['teacher'].strip()
        qs = User.objects.filter(full_name__iexact=name, role=Role.TEACHER, is_active=True)
        if not qs.exists():
            raise ValidationError(
                _('Викладача «%(name)s» не знайдено. Перевірте ПІБ.'),
                params={'name': name},
            )
        if qs.count() > 1:
            raise ValidationError(
                _('Знайдено кількох викладачів з іменем «%(name)s». Уточніть ПІБ.'),
                params={'name': name},
            )
        return qs.first()

    def clean_group(self):
        name = self.cleaned_data['group'].strip()
        try:
            return Group.objects.get(name__iexact=name)
        except Group.DoesNotExist:
            raise ValidationError(
                _('Групу «%(name)s» не знайдено.'),
                params={'name': name},
            )

    def clean_subgroup(self):
        subgroup = self.cleaned_data.get('subgroup')
        return subgroup or None

    def clean_parallel_teacher(self):
        name = self.cleaned_data.get('parallel_teacher', '').strip()
        if not self.cleaned_data.get('create_parallel_subgroup'):
            return None
        if not name:
            raise ValidationError(_('Потрібно вказати викладача для паралельної підгрупи.'))

        qs = User.objects.filter(full_name__iexact=name, role=Role.TEACHER, is_active=True)
        if not qs.exists():
            raise ValidationError(
                _('Викладача «%(name)s» не знайдено. Перевірте ПІБ.'),
                params={'name': name},
            )
        if qs.count() > 1:
            raise ValidationError(
                _('Знайдено кількох викладачів з іменем «%(name)s». Уточніть ПІБ.'),
                params={'name': name},
            )
        return qs.first()

    def clean_parallel_lesson_number(self):
        raw_value = self.cleaned_data.get('parallel_lesson_number', '')
        if raw_value in ('', None):
            return None
        return int(raw_value)

    def clean_lesson_number(self):
        return int(self.cleaned_data['lesson_number'])

    def clean_weekday(self):
        return int(self.cleaned_data['weekday'])

    def clean(self):
        cleaned = super().clean()
        semester = cleaned.get('semester')
        weekday = cleaned.get('weekday')
        lesson_number = cleaned.get('lesson_number')
        week_type = cleaned.get('week_type')
        teacher = cleaned.get('teacher')
        group = cleaned.get('group')
        lesson_type = cleaned.get('lesson_type')
        subgroup = cleaned.get('subgroup')
        create_parallel = cleaned.get('create_parallel_subgroup')
        parallel_teacher = cleaned.get('parallel_teacher')
        parallel_lesson_number = cleaned.get('parallel_lesson_number')

        if lesson_type != LessonType.LAB and subgroup:
            self.add_error('subgroup', _('Підгрупа може бути задана тільки для лабораторних занять.'))

        if lesson_type == LessonType.LAB and create_parallel and not subgroup:
            self.add_error('subgroup', _('Потрібно вибрати підгрупу для основної лабораторної пари перед створенням паралельної.'))

        if create_parallel and lesson_type != LessonType.LAB:
            self.add_error('create_parallel_subgroup', _('Паралельну підгрупу можна створювати лише для лабораторних занять.'))

        if create_parallel and not parallel_teacher:
            self.add_error('parallel_teacher', _('Потрібно вказати викладача для паралельної підгрупи.'))

        if not all([semester, weekday is not None, lesson_number, week_type, teacher, group, lesson_type]):
            return cleaned

        exclude_pk = self.instance.pk if self.instance and self.instance.pk else None
        conflicts = get_conflicts(
            semester=semester,
            weekday=weekday,
            lesson_number=lesson_number,
            week_type=week_type,
            teacher_id=teacher.pk,
            group_id=group.pk,
            lesson_type=lesson_type,
            subgroup=subgroup,
            exclude_pk=exclude_pk,
        )

        if conflicts['teacher']:
            conflicting = conflicts['teacher'][0]
            self.add_error(None, ValidationError(
                _('Викладач %(teacher)s вже має пару %(num)s у %(day)s (%(wt)s тиждень): %(subj)s — %(group)s'),
                params={
                    'teacher': teacher.full_name,
                    'num': lesson_number,
                    'day': Weekday(weekday).label,
                    'wt': WeekType(week_type).label,
                    'subj': conflicting.subject.name,
                    'group': conflicting.group.name,
                },
                code='teacher_conflict',
            ))

        if conflicts['group']:
            conflicting = conflicts['group'][0]
            self.add_error(None, ValidationError(
                _('Група %(group)s вже має пару %(num)s у %(day)s (%(wt)s тиждень): %(subj)s — %(teacher)s'),
                params={
                    'group': group.name,
                    'num': lesson_number,
                    'day': Weekday(weekday).label,
                    'wt': WeekType(week_type).label,
                    'subj': conflicting.subject.name,
                    'teacher': conflicting.teacher.full_name,
                },
                code='group_conflict',
            ))

        if create_parallel and parallel_teacher:
            parallel_subgroup = 'B' if subgroup == 'A' else 'A'
            parallel_lesson_number = parallel_lesson_number or lesson_number
            parallel_conflicts = get_conflicts(
                semester=semester,
                weekday=weekday,
                lesson_number=parallel_lesson_number,
                week_type=week_type,
                teacher_id=parallel_teacher.pk,
                group_id=group.pk,
                lesson_type=LessonType.LAB,
                subgroup=parallel_subgroup,
                exclude_pk=exclude_pk,
            )
            if parallel_conflicts['teacher']:
                conflicting = parallel_conflicts['teacher'][0]
                self.add_error('parallel_teacher', ValidationError(
                    _('Викладач для паралельної підгрупи вже зайнятий у %(num)s парі на %(day)s (%(wt)s тиждень): %(subj)s — %(group)s'),
                    params={
                        'num': parallel_lesson_number,
                        'day': Weekday(weekday).label,
                        'wt': WeekType(week_type).label,
                        'subj': conflicting.subject.name,
                        'group': conflicting.group.name,
                    },
                    code='teacher_conflict',
                ))
            if parallel_conflicts['group']:
                self.add_error('parallel_lesson_number', ValidationError(
                    _('Паралельна підгрупа вже має пару %(num)s у %(day)s (%(wt)s тиждень).'),
                    params={
                        'num': parallel_lesson_number,
                        'day': Weekday(weekday).label,
                        'wt': WeekType(week_type).label,
                    },
                    code='group_conflict',
                ))

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subject = self.cleaned_data['subject']
        instance.teacher = self.cleaned_data['teacher']
        instance.group = self.cleaned_data['group']
        instance.subgroup = self.cleaned_data.get('subgroup')
        instance.classroom = self.cleaned_data.get('classroom', '')
        if instance.lesson_number in LESSON_TIMES:
            instance.start_time, instance.end_time = LESSON_TIMES[instance.lesson_number]

        parallel_teacher = self.cleaned_data.get('parallel_teacher')
        parallel_lesson_number = self.cleaned_data.get('parallel_lesson_number') or instance.lesson_number
        parallel_classroom = self.cleaned_data.get('parallel_classroom') or instance.classroom
        create_parallel = self.cleaned_data.get('create_parallel_subgroup')

        with transaction.atomic():
            if commit:
                instance.save()
            if create_parallel and parallel_teacher:
                parallel_subgroup = 'B' if instance.subgroup == 'A' else 'A'
                parallel_instance = Schedule(
                    subject=instance.subject,
                    teacher=parallel_teacher,
                    group=instance.group,
                    semester=instance.semester,
                    lesson_type=instance.lesson_type,
                    weekday=instance.weekday,
                    lesson_number=parallel_lesson_number,
                    week_type=instance.week_type,
                    subgroup=parallel_subgroup,
                    classroom=parallel_classroom,
                )
                if parallel_instance.lesson_number in LESSON_TIMES:
                    parallel_instance.start_time, parallel_instance.end_time = LESSON_TIMES[parallel_instance.lesson_number]
                parallel_instance.full_clean()
                parallel_instance.save()
        return instance


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Математичний аналіз'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': _('Назва предмету'),
            'description': _('Опис'),
        }


class ScheduleFilterForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.order_by('-start_date'),
        required=False,
        empty_label=_('Всі семестри'),
        label=_('Семестр'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.order_by('course', 'name'),
        required=False,
        empty_label=_('Всі групи'),
        label=_('Група'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(role=Role.TEACHER).order_by('full_name'),
        required=False,
        empty_label=_('Всі викладачі'),
        label=_('Викладач'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    week_type = forms.ChoiceField(
        choices=[('', _('Обидва тижні'))] + list(WeekType.choices),
        required=False,
        label=_('Тиждень'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
    weekday = forms.ChoiceField(
        choices=[('', _('Всі дні'))] + list(Weekday.choices),
        required=False,
        label=_('День'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
