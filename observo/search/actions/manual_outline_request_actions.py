from django.conf import settings
from django.contrib import admin, messages

from search.models import Match, Notification, Website
from search.tasks import prepare_single_outline, scrape_website


def _get_or_create_website_by_url(url: str) -> Website:
    """
    Return the first Website with the given URL or create a new one if none exists.
    This avoids MultipleObjectsReturned when duplicates are present.
    """
    website = Website.objects.filter(url=url).order_by("pk").first()
    if not website:
        website = Website.objects.create(url=url)
    return website


@admin.action(description="Fetch summary from URL")
def fetch_summary_for_requests(model_admin, request, queryset) -> None:
    scheduled = 0
    for req in queryset:
        if not req.website_url:
            model_admin.message_user(request, f"Request #{req.pk} has no Website URL.", level=messages.WARNING)
            continue
        website = _get_or_create_website_by_url(req.website_url)
        scrape_website.delay(website.pk)
        scheduled += 1
    model_admin.message_user(request, f"Scheduled summary fetch for {scheduled} request(s).")


@admin.action(description="Generate single outline")
def generate_outline_for_requests(model_admin, request, queryset) -> None:
    scheduled = 0
    for req in queryset:
        if not req.summary:
            model_admin.message_user(
                request,
                f"Request #{req.pk} has empty summary; fetch or paste a summary first.",
                level=messages.WARNING,
            )
            continue

        website = None
        if req.website_url:
            website = _get_or_create_website_by_url(req.website_url)
            if not website.summary:
                website.summary = req.summary
                website.save()
        else:
            website = Website.objects.create(summary=req.summary)

        match = Match.objects.filter(website=website).order_by("-created_at").first()
        if not match:
            match = Match.objects.create(website=website)

        default_email = getattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "anonymous@open-grant.com")
        notification = Notification.objects.create(match=match, email=req.email or default_email)

        prepare_single_outline.delay(notification.pk, str(req.opportunity.id))
        scheduled += 1

    if scheduled:
        model_admin.message_user(request, f"Scheduled {scheduled} outline(s).")
    else:
        model_admin.message_user(request, "No outlines were scheduled.", level=messages.WARNING)
