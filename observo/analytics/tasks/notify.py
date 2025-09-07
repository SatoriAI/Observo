from celery import shared_task

from analytics.models import Contact
from utils.mailer import send_email


@shared_task(name="notify_contact")
def notify_contact(contact_id: int) -> None:
    contact = Contact.objects.get(id=contact_id)

    send_email(
        subject="[OpenGrant] Schedule your grant strategy call",
        recipients=[contact.email],
        cc=["casper@open-grant.com"],
        template="email/notify.html",
        context={"contact": contact},
    )

    contact.notified = True
    contact.save()
