import logging
import time

from celery import shared_task

from analytics.models import Contact
from utils.functions import get_time_based_greeting
from utils.mailer import send_email

logger = logging.getLogger(__name__)


@shared_task(name="notify_contact")
def notify_contact(contact_id: int) -> None:
    logger.info(f"Starting notify_contact task for contact_id: {contact_id}")

    try:
        # Retrieve contact with retry logic for Railway startup issues
        contact = None
        retry_delays = [2, 4, 8, 16, 32]  # Exponential backoff in seconds

        for attempt in range(len(retry_delays) + 1):
            try:
                contact = Contact.objects.get(id=contact_id)
                logger.info(
                    f"Retrieved contact on attempt {attempt + 1} - ID: {contact.id}, Email: {contact.email}, Name: {getattr(contact, 'name', 'N/A')}"
                )
                break  # Success, exit retry loop
            except Contact.DoesNotExist:
                if attempt < len(retry_delays):
                    delay = retry_delays[attempt]
                    logger.warning(f"Contact {contact_id} not found on attempt {attempt + 1}, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # This was the last attempt, re-raise the exception
                    raise
            except Exception as e:
                if attempt < len(retry_delays):
                    delay = retry_delays[attempt]
                    logger.warning(f"Error retrieving contact {contact_id} on attempt {attempt + 1}: {str(e)}, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # This was the last attempt, re-raise the exception
                    raise

        # If we get here without a contact, something went wrong with the retry logic
        if contact is None:
            raise Contact.DoesNotExist(f"Failed to retrieve contact {contact_id} after all retry attempts")

        # Log email preparation details
        recipients = [contact.email]
        cc_list = ["casper@open-grant.com"]
        logger.info(
            f"Preparing to send email - Recipients: {recipients}, CC: {cc_list}, Subject: '[OpenGrant] Schedule your grant strategy call'"
        )

        # Generate time-based greeting based on user's locale
        greeting = get_time_based_greeting(locale=contact.survey.locale)

        # Send the email
        logger.info(f"Sending notification email to contact {contact_id} with greeting: '{greeting}'")
        send_email(
            subject="[OpenGrant] Schedule your grant strategy call",
            recipients=recipients,
            cc=cc_list,
            template="email/notify.html",
            context={"contact": contact, "greeting": greeting},
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
