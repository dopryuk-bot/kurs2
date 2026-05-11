from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Role, TeacherProfile, User


@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    """
    Automatically creates TeacherProfile when a Teacher user is first saved.
    StarostaProfile requires a group assignment, so it's created manually.
    """
    if created and instance.role == Role.TEACHER:
        TeacherProfile.objects.get_or_create(user=instance)
