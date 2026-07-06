from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Ensures a UserProfile exists for every User.
    Uses get_or_create to prevent IntegrityErrors during Admin user creation.
    """
    UserProfile.objects.get_or_create(user=instance)
    instance.profile.save()
