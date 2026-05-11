from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager


class Role(models.TextChoices):
    ADMIN = 'admin', _('Адміністратор')
    TEACHER = 'teacher', _('Викладач')
    STAROSTA = 'starosta', _('Староста')


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Email is the unique identifier instead of username.
    Role determines which dashboard and permissions the user gets.
    """

    email = models.EmailField(_('email'), unique=True)
    full_name = models.CharField(_('ПІБ'), max_length=200)
    role = models.CharField(_('роль'), max_length=10, choices=Role.choices)
    is_active = models.BooleanField(_('активний'), default=True)
    is_staff = models.BooleanField(_('персонал'), default=False)
    created_at = models.DateTimeField(_('створено'), auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('користувач')
        verbose_name_plural = _('користувачі')
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'

    def get_short_name(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return f'{parts[0]} {parts[1][0]}.'
        return self.full_name

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_starosta(self):
        return self.role == Role.STAROSTA

    def get_dashboard_url(self):
        from django.urls import reverse
        role_map = {
            Role.ADMIN: 'dashboard:admin:index',
            Role.TEACHER: 'dashboard:teacher:index',
            Role.STAROSTA: 'dashboard:starosta:index',
        }
        return reverse(role_map[self.role])


class TeacherProfile(models.Model):
    """
    Extended profile for users with role=TEACHER.
    Created automatically when a Teacher user is saved.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name=_('користувач'),
        limit_choices_to={'role': Role.TEACHER},
    )
    department = models.CharField(_('кафедра'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('профіль викладача')
        verbose_name_plural = _('профілі викладачів')

    def __str__(self):
        return f'{self.user.full_name}'


class StarostaProfile(models.Model):
    """
    Extended profile for users with role=STAROSTA.
    A group can have at most 2 starostas (enforced in clean()).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='starosta_profile',
        verbose_name=_('користувач'),
        limit_choices_to={'role': Role.STAROSTA},
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        related_name='starostas',
        verbose_name=_('група'),
    )

    class Meta:
        verbose_name = _('профіль старости')
        verbose_name_plural = _('профілі старост')
        unique_together = [('user', 'group')]

    def __str__(self):
        return f'{self.user.full_name} → {self.group}'

    def clean(self):
        if self.group_id:
            existing_count = StarostaProfile.objects.filter(
                group=self.group_id
            ).exclude(pk=self.pk).count()
            if existing_count >= 2:
                raise ValidationError(
                    _('У групі %(group)s вже є 2 старости. Максимально допустимо 2.'),
                    params={'group': self.group},
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
