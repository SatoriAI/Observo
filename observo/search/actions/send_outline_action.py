from django.contrib import admin

from search.tasks import send_outline_notification


@admin.action(description="Send Outline to Owners")
def send_outline_to_owner_markdown(model_admin, request, queryset) -> None:
    owners = []
    for notification in queryset:
        if not notification.owner:
            model_admin.message_user(request, "No Owners found!")
            return
        send_outline_notification(notification.pk, notification.owner)
        owners.append(notification.owner)
    model_admin.message_user(request, f"Successfully send {queryset.count()} Notification(s) to {", ".join(owners)}.")


@admin.action(description="Send Outline to Users")
def send_outline_to_email_markdown(model_admin, request, queryset) -> None:
    emails = []
    for notification in queryset:
        send_outline_notification.delay(notification.pk, notification.email)
        emails.append(notification.email)
    model_admin.message_user(request, f"Successfully send {queryset.count()} Notification(s) to {", ".join(emails)}.")
