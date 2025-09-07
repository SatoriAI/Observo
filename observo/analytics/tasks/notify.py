import logging

from celery import shared_task

from analytics.models import Contact
from utils.mailer import send_email

logger = logging.getLogger(__name__)


@shared_task(name="notify_contact")
def notify_contact(contact_id: int) -> None:
    logger.info(f"Starting notify_contact task for contact_id: {contact_id}")

    try:
        # Retrieve contact with extended logging
        contact = Contact.objects.get(id=contact_id)
        logger.info(
            f"Retrieved contact - ID: {contact.id}, Email: {contact.email}, Name: {getattr(contact, 'name', 'N/A')}"
        )

        # Log email preparation details
        recipients = [contact.email]
        cc_list = ["casper@open-grant.com"]
        logger.info(
            f"Preparing to send email - Recipients: {recipients}, CC: {cc_list}, Subject: '[OpenGrant] Schedule your grant strategy call'"
        )

        # Send the email
        logger.info(f"Sending notification email to contact {contact_id}")
        send_email(
            subject="[OpenGrant] Schedule your grant strategy call",
            recipients=recipients,
            cc=cc_list,
            template="email/notify.html",
            context={"contact": contact},
        )
        logger.info(f"Email sent successfully to contact {contact_id} ({contact.email})")

        # Update contact status
        contact.notified = True
        contact.save()
        logger.info(f"Contact {contact_id} marked as notified and saved successfully")

        logger.info(f"notify_contact task completed successfully for contact_id: {contact_id}")

    except Contact.DoesNotExist:
        logger.error(f"Contact with ID {contact_id} does not exist")
        raise
    except Exception as e:
        logger.error(f"Error in notify_contact task for contact_id {contact_id}: {str(e)}", exc_info=True)
        raise
