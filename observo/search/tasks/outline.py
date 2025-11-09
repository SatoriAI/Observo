import logging
from uuid import UUID

from celery import chain, shared_task
from django.conf import settings
from lorem_text import lorem
from opportunity.models import Opportunity

from search.enums import Workflows
from search.models import Match, Notification, Outline, Website, Workflow
from search.tasks import send_post_generation_notification
from search.tasks.match import match_proposals

logger = logging.getLogger(__name__)


@shared_task(name="single_outline")
def prepare_single_outline(notification_pk: int, opportunity_id: str) -> None:
    notification = Notification.objects.get(pk=notification_pk)
    logger.info(f"Preparing single Outline for Notification #{notification_pk} and Opportunity {opportunity_id}")

    website = notification.match.website if notification.match else None
    summary = getattr(website, "summary", None) if website else None
    if not summary:
        logger.warning(f"Notification #{notification_pk} has no website summary; cannot generate outline.")
        return

    opportunity = Opportunity.objects.get(pk=opportunity_id)
    outline = Outline.objects.create(
        opportunity=opportunity,
        notification=notification,
        title=opportunity.title,
        content=get_content(summary=summary, identifier=opportunity.id, debug=False),
    )
    logger.info(f"Outline #{outline.pk} created successfully (single outline mode)")

    notification.set_ready()
    send_post_generation_notification.delay(notification.pk)


@shared_task(name="outline")
def prepare_outline(pk: int) -> None:
    notification = Notification.objects.get(pk=pk)
    logger.info(f"Preparing Outline for: {notification.email} (Notification #{pk})")

    summary = notification.match.website.summary
    logger.debug(f"Summary for Notification #{pk}: {summary.split(" ")[:10]}")

    proposals = notification.match.proposals
    logger.debug(f"Proposals for Notification #{pk}")

    for grant in proposals:
        logger.info(f"Working in Grant #{grant["id"]}")
        outline = Outline.objects.create(
            opportunity=Opportunity.objects.get(pk=grant["id"]),
            notification=notification,
            title=grant["title"],
            content=get_content(summary=summary, identifier=grant["id"], debug=False),
        )
        logger.info(f"Outline #{outline.pk} created successfully")

    notification.set_ready()
    send_post_generation_notification.delay(notification.pk)


def get_content(summary: str, identifier: UUID, debug: bool = False) -> str | None:
    if debug:
        return lorem.paragraphs(3)

    opportunity = Opportunity.objects.get(id=identifier)
    workflow = Workflow.objects.filter(title=Workflows.OUTLINE_PREPARER).first()

    return workflow.process(context={"summary": summary, "opportunity": opportunity.describe()}, logger=logger)


@shared_task(name="auto_prepare_outline_for_website")
def auto_prepare_outline_for_website(website_pk: int) -> None:
    website = Website.objects.filter(pk=website_pk).first()
    if not website:
        logger.error(f"Website #{website_pk} not found")
        return

    if not website.summary:
        # Summary not ready yet; skip for now
        logger.info(f"Website #{website_pk} has no summary yet; skipping auto outline")
        return

    match = Match.objects.filter(website=website).order_by("-created_at").first()
    if not match:
        match = Match.objects.create(website=website)

    # Reuse any existing Notification for this website; otherwise create one for the selected match
    notification = Notification.objects.filter(match__website=website).order_by("-created_at").first()
    if not notification:
        default_email = getattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "anonymous@open-grant.com")
        notification = Notification.objects.create(match=match, email=default_email)
    elif notification.match_id != match.id and not notification.ready:
        # Point the existing notification to the latest match if outlines aren't ready
        notification.match = match
        notification.save()

    # If outlines are already prepared, do nothing
    if notification.ready or notification.outlines.exists():
        logger.info(f"Notification #{notification.pk} already has outlines or is ready; skipping auto outline")
        return

    # Ensure proposals exist; if not, match first then prepare outlines
    if not match.proposals:
        logger.info(
            f"Scheduling match then outline for Website #{website_pk} (Match #{match.pk}, Notification #{notification.pk})"
        )
        chain(
            match_proposals.s(match.pk, website.summary, True, 3),
            prepare_outline.si(notification.pk),
        ).delay()
        return

    logger.info(f"Scheduling outline for Notification #{notification.pk} (Website #{website_pk})")
    prepare_outline.delay(notification.pk)
