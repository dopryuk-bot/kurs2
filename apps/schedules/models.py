from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class LessonType(models.TextChoices):
    LECTURE = 'lecture', _('Лекція')
    LAB = 'lab', _('Лабораторна')
    PRACTICE = 'practice', _('Практика')


class WeekType(models.TextChoices):
    ODD = 'ODD', _('Непарний')
    EVEN = 'EVEN', _('Парний')


class Subgroup(models.TextChoices):
    A = 'A', _('A')
    B = 'B', _('B')


class Weekday(models.IntegerChoices):
    MONDAY = 0, _('Понеділок')
    TUESDAY = 1, _('Вівторок')
    WEDNESDAY = 2, _('Середа')
    THURSDAY = 3, _('Четвер')
    FRIDAY = 4, _('П\'ятниця')
    SATURDAY = 5, _('Субота')


class Subject(models.Model):
    """Academic subject/course (e.g. Математичний аналіз, Програмування)."""

    name = models.CharField(_('назва'), max_length=200)
    description = models.TextField(_('опис'), blank=True)

    class Meta:
        verbose_name = _('предмет')
        verbose_name_plural = _('предмети')
        ordering = ['name']

    def __str__(self):
        return self.name


class Semester(models.Model):
    """
    Academic semester. Only one can be active at a time (enforced via DB constraint).
    first_study_week_date must be a Monday — it is the anchor for ODD/EVEN calculation.
    Week 1 is always ODD per university policy.
    """

    name = models.CharField(_('назва'), max_length=100)
    start_date = models.DateField(_('дата початку'))
    end_date = models.DateField(_('дата завершення'))
    first_study_week_date = models.DateField(
        _('дата першого навчального тижня'),
        help_text=_('Понеділок першого навчального тижня. Тиждень 1 = непарний.'),
    )
    is_active = models.BooleanField(_('активний'), default=False)

    class Meta:
        verbose_name = _('семестр')
        verbose_name_plural = _('семестри')
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_semester',
            )
        ]

    def __str__(self):
        return self.name

    def get_week_number(self, target_date):
        """
        Returns the 1-indexed academic week number for a given date.
        Returns None if the date is before the semester starts.
        """
        delta = (target_date - self.first_study_week_date).days
        if delta < 0:
            return None
        return delta // 7 + 1

    def get_week_type(self, target_date):
        """
        Returns WeekType.ODD or WeekType.EVEN.
        Week 1 is ODD, week 2 is EVEN, and so on.
        Returns None if the date is before the semester starts.
        """
        week_number = self.get_week_number(target_date)
        if week_number is None:
            return None
        return WeekType.ODD if week_number % 2 != 0 else WeekType.EVEN

    def contains_date(self, target_date):
        return self.start_date <= target_date <= self.end_date


class Schedule(models.Model):
    """
    A recurring weekly lesson slot. Represents the timetable pattern, not a specific date.
    The combination of (group, semester, weekday, lesson_number, week_type) must be unique
    to prevent timetable conflicts.
    """

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('предмет'),
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('викладач'),
        limit_choices_to={'role': 'teacher'},
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('група'),
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('семестр'),
    )
    lesson_type = models.CharField(
        _('тип заняття'),
        max_length=10,
        choices=LessonType.choices,
    )
    weekday = models.PositiveSmallIntegerField(
        _('день тижня'),
        choices=Weekday.choices,
    )
    lesson_number = models.PositiveSmallIntegerField(
        _('номер пари'),
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    week_type = models.CharField(
        _('тип тижня'),
        max_length=4,
        choices=WeekType.choices,
    )
    subgroup = models.CharField(
        _('підгрупа'),
        max_length=1,
        choices=Subgroup.choices,
        null=True,
        blank=True,
        help_text=_('Підгрупа застосовується лише для лабораторних занять.'),
    )
    classroom = models.CharField(_('аудиторія'), max_length=50, blank=True)
    start_time = models.TimeField(_('початок'))
    end_time = models.TimeField(_('кінець'))

    class Meta:
        verbose_name = _('розклад')
        verbose_name_plural = _('розклад')
        ordering = ['weekday', 'lesson_number']
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'semester', 'weekday', 'lesson_number', 'week_type'],
                condition=models.Q(subgroup__isnull=True),
                name='unique_schedule_no_subgroup',
            ),
            models.UniqueConstraint(
                fields=['group', 'semester', 'weekday', 'lesson_number', 'week_type', 'subgroup'],
                condition=models.Q(subgroup__isnull=False),
                name='unique_schedule_with_subgroup',
            ),
        ]

    def __str__(self):
        weekday_name = Weekday(self.weekday).label
        subgroup_label = f' {self.subgroup}' if self.subgroup else ''
        return (
            f'{self.subject} — {self.group}{subgroup_label} — '
            f'{weekday_name} — пара {self.lesson_number} ({self.week_type})'
        )

    @property
    def subgroup_label(self):
        if self.subgroup:
            return f'LAB {self.subgroup}'
        return ''

    def clean(self):
        if self.lesson_type != LessonType.LAB and self.subgroup:
            raise ValidationError({
                'subgroup': _('Підгрупа може бути задана тільки для лабораторних занять.'),
            })
        return super().clean()

    def get_lesson_type_badge_class(self):
        badge_map = {
            LessonType.LECTURE: 'bg-primary',
            LessonType.LAB: 'bg-success',
            LessonType.PRACTICE: 'bg-warning',
        }
        return badge_map.get(self.lesson_type, 'bg-secondary')
