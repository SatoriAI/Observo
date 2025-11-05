from celery import chain
from django.conf import settings
from django.contrib import admin

from search.models import Match, Notification
from search.tasks import prepare_outline
from search.tasks.match import match_proposals


@admin.action(description="Create Notification and Prepare Outline")
def create_notification_and_prepare_outline(model_admin, request, queryset) -> None:
    scheduled = 0
    created = 0

    for website in queryset:
        match = Match.objects.filter(website=website).order_by("-created_at").first()
        if not match:
            match = Match.objects.create(website=website)

        default_email = getattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "anonymous@open-grant.com")
        notification = Notification.objects.create(match=match, email=default_email)
        created += 1

        # If there's no summary yet, we cannot match or generate outlines now
        if not getattr(website, "summary", None):
            continue

        # Match proposals first if needed, then prepare outlines
        if not match.proposals:
            chain(
                match_proposals.s(match.pk, website.summary, True, 3),
                prepare_outline.si(notification.pk),
            ).delay()
        else:
            prepare_outline.delay(notification.pk)

        scheduled += 1

    msg = f"Created {created} Notification(s). " f"Scheduled outline preparation for {scheduled} Website(s)."
    model_admin.message_user(request, msg)
