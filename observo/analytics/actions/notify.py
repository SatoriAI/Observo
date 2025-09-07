from django.contrib import messages
from django.utils.translation import ngettext

from analytics.models import Contact
from analytics.tasks.notify import notify_contact


def notify_selected_contacts(modeladmin, request, queryset):
    """
    Admin action to notify selected contacts by scheduling notification tasks.

    This action will:
    1. Filter out contacts that have already been notified
    2. Schedule notification tasks for remaining contacts
    3. Show appropriate success/error messages
    """
    contacts_to_notify = queryset.filter(notified=False)

    if not contacts_to_notify.exists():
        messages.warning(
            request,
            "All selected contacts have already been notified."
        )
        return

    # Count how many contacts we're processing
    total_contacts = contacts_to_notify.count()
    notified_count = 0
    failed_count = 0

    # Schedule notification tasks for each contact
    for contact in contacts_to_notify:
        try:
            # Schedule the notification task asynchronously
            notify_contact.delay(contact.id)
            notified_count += 1
        except Exception as e:
            failed_count += 1
            modeladmin.message_user(
                request,
                f"Failed to schedule notification for {contact.email}: {str(e)}",
                level=messages.ERROR
            )

    # Show success message
    if notified_count > 0:
        message = ngettext(
            "%d contact notification has been scheduled.",
            "%d contact notifications have been scheduled.",
            notified_count,
        ) % notified_count

        if failed_count > 0:
            message += f" {failed_count} failed to schedule."

        modeladmin.message_user(
            request,
            message,
            level=messages.SUCCESS if failed_count == 0 else messages.WARNING
        )


# Set the action description for the admin interface
notify_selected_contacts.short_description = "Notify selected contacts"
