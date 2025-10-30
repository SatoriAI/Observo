from django.contrib import admin

from search.tasks import prepare_outline


@admin.action(description="Rerun Workflow for Selected Outlines")
def rerun_generation(model_admin, request, queryset) -> None:
    for notification in queryset:
        prepare_outline.delay(notification.pk)
    model_admin.message_user(request, f"Preparation reran for {queryset.count()} Notifications.")
