from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', _('Присутній')
    ABSENT = 'ABSENT', _('Відсутній')
    EXCUSED = 'EXCUSED', _('Поважна причина')
    LATE = 'LATE', _('Запізнився')


class Attendance(models.Model):
    """
    A single attendance record: one student, one lesson, one date.
    The unique_together constraint ensures no duplicates per lesson session.
    Default status is PRESENT — starosta marks only absences/late.
    marked_by tracks accountability: who last changed this record.
    """

    student = models.ForeignKey(
        'groups.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_('студент'),
    )
    schedule = models.ForeignKey(
        'schedules.Schedule',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_('пара'),
    )
    date = models.DateField(_('дата'))
    status = models.CharField(
        _('статус'),
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances',
        verbose_name=_('відмітив'),
    )
    updated_at = models.DateTimeField(_('оновлено'), auto_now=True)

    class Meta:
        verbose_name = _('відвідування')
        verbose_name_plural = _('відвідування')
        unique_together = [('student', 'schedule', 'date')]
        ordering = ['date', 'student__full_name']
        indexes = [
            models.Index(fields=['date', 'schedule']),
            models.Index(fields=['student', 'date']),
        ]

    def __str__(self):
        return f'{self.student} — {self.date} — {self.get_status_display()}'

    def get_status_badge_class(self):
        badge_map = {
            AttendanceStatus.PRESENT: 'bg-success',
            AttendanceStatus.ABSENT: 'bg-danger',
            AttendanceStatus.EXCUSED: 'bg-warning text-dark',
            AttendanceStatus.LATE: 'bg-info text-dark',
        }
        return badge_map.get(self.status, 'bg-secondary')
