from django.contrib import admin, messages
from django.utils.translation import ngettext

from analytics.tasks.notify import notify_contact


@admin.action(description="Notify selected contacts")
def notify_selected_contacts(modeladmin, request, queryset):
    contacts_to_notify = queryset.filter(notified=False)

    if not contacts_to_notify.exists():
        messages.warning(request, "All selected contacts have already been notified.")
        return

    notified_count = 0
    failed_count = 0

    for contact in contacts_to_notify:
        try:
            notify_contact.delay(contact.id)
            notified_count += 1
        except Exception as e:
            failed_count += 1
            modeladmin.message_user(
                request, f"Failed to schedule notification for {contact.email}: {str(e)}", level=messages.ERROR
            )

    if notified_count > 0:
        message = (
            ngettext(
                "%d contact notification has been scheduled.",
                "%d contact notifications have been scheduled.",
                notified_count,
            )
            % notified_count
        )

        if failed_count > 0:
            message += f" {failed_count} failed to schedule."

        modeladmin.message_user(request, message, level=messages.SUCCESS if failed_count == 0 else messages.WARNING)
