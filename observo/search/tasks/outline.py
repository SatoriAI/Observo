import logging
from uuid import UUID

from celery import shared_task
from lorem_text import lorem

from search.models import Notification, Outline

logger = logging.getLogger(__name__)


@shared_task(name="outline")
def prepare_outline(pk: int) -> None:
    notification = Notification.objects.get(pk=pk)
    logger.info(f"Preparing Outline for: {notification.email} (Notification #{pk})")

    summary = notification.match.website.summary
    logger.debug(f"Summary for Notification #{pk}: {summary.split(" ")[:10]}")

    proposals = notification.match.proposals
    logger.debug(f"Proposals for Notification #{pk}")

    for grant in proposals:
        outline = Outline.objects.create(
            notification=notification,
            title=grant["title"],
            content=get_content(summary=summary, identifier=grant["id"], debug=True),
        )
        logger.info(f"Outline #{outline.pk} created successfully")

    notification.set_ready()


def get_content(summary: str, identifier: UUID, debug: bool = False) -> str:
    if debug:
        return lorem.paragraphs(3)
