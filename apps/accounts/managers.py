from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager that uses email instead of username as the unique identifier.
    """

    def create_user(self, email, full_name, role, password=None, **extra_fields):
        if not email:
            raise ValueError('Email є обов\'язковим полем')
        if not full_name:
            raise ValueError('ПІБ є обов\'язковим полем')
        if not role:
            raise ValueError('Роль є обов\'язковим полем')

        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        from apps.accounts.models import Role

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, full_name, Role.ADMIN, password, **extra_fields)

    def teachers(self):
        from apps.accounts.models import Role
        return self.filter(role=Role.TEACHER, is_active=True)

    def starostas(self):
        from apps.accounts.models import Role
        return self.filter(role=Role.STAROSTA, is_active=True)

    def admins(self):
        from apps.accounts.models import Role
        return self.filter(role=Role.ADMIN, is_active=True)
