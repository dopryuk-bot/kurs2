from django.contrib.auth.backends import ModelBackend

from apps.accounts.models import User


class EmailBackend(ModelBackend):
    """
    Authenticates using email + password instead of username + password.
    Used as the sole authentication backend in settings.AUTHENTICATION_BACKENDS.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
