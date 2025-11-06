from django.db.models.signals import post_save
from django.dispatch import receiver

from analytics.models import Contact, Survey
from analytics.tasks import notify_contact, notify_new_survey


@receiver(post_save, sender=Contact)
def notify_contact_on_save(sender, instance, created, **kwargs):
    if created and not instance.notified:
        notify_contact.delay(instance.id)


@receiver(post_save, sender=Survey)
def notify_survey_on_save(sender, instance, created, **kwargs):
    if created:
        notify_new_survey.delay(instance.id)
