from django.db.models.signals import post_save
from django.dispatch import receiver

from analytics.models import Contact


@receiver(post_save, sender=Contact)
def notify_contact_on_save(sender, instance, created, **kwargs):
    if created and not instance.notified:
        from analytics.tasks.notify import notify_contact

        notify_contact.delay(instance.id)
