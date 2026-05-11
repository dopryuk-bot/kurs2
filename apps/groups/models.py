from django.db import models
from django.utils.translation import gettext_lazy as _


class Subgroup(models.TextChoices):
    A = 'A', _('А')
    B = 'B', _('Б')


class Group(models.Model):
    """
    Academic group (e.g. КН-31, МТ-21).
    Students belong to a group; starostas are linked via StarostaProfile.
    """

    name = models.CharField(_('назва'), max_length=50, unique=True)
    course = models.PositiveSmallIntegerField(_('курс'))
    created_at = models.DateTimeField(_('створено'), auto_now_add=True)

    class Meta:
        verbose_name = _('група')
        verbose_name_plural = _('групи')
        ordering = ['course', 'name']

    def __str__(self):
        return self.name

    def get_active_students(self):
        return self.students.filter(is_active=True).order_by('full_name')

    def get_starostas(self):
        return self.starostas.select_related('user').all()


class Student(models.Model):
    """
    A student belongs to exactly one group. No auth account — identified by full name only.
    is_active allows soft-deletion (e.g. student left the university).
    subgroup is used for dividing lab groups into A/B subgroups.
    """

    full_name = models.CharField(_('ПІБ'), max_length=200)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name=_('група'),
    )
    subgroup = models.CharField(
        _('підгрупа'),
        max_length=1,
        choices=Subgroup.choices,
        blank=True,
        null=True,
        help_text=_('Використовується для розподілу на лабораторні роботи'),
    )
    is_active = models.BooleanField(_('активний'), default=True)

    class Meta:
        verbose_name = _('студент')
        verbose_name_plural = _('студенти')
        ordering = ['full_name']
        unique_together = [('full_name', 'group')]

    def __str__(self):
        return self.full_name
    
    def get_subgroup_display_short(self):
        if self.subgroup:
            return f'({self.subgroup})'
        return ''
