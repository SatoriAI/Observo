import logging
from uuid import UUID

from celery import shared_task
from lorem_text import lorem
from opportunity.models import Opportunity

from search.models import Notification, Outline, Workflow
from utils.clients import GeminiClient

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
        logger.info(f"Working in Grant #{grant["id"]}")
        outline = Outline.objects.create(
            notification=notification,
            title=grant["title"],
            content=get_content(summary=summary, identifier=grant["id"], debug=False),
        )
        logger.info(f"Outline #{outline.pk} created successfully")

    notification.set_ready()


def get_content(summary: str, identifier: UUID, debug: bool = False) -> str | None:
    if debug:
        return lorem.paragraphs(3)

    opportunity = Opportunity.objects.get(id=identifier)
    workflow = Workflow.objects.first()

    context = {"summary": summary, "opportunity": opportunity.describe()}

    generated = None

    for prompt in workflow.prompts.all():
        logger.info(f"Processing Prompt {prompt.name} (#{prompt.pk})")

        gemini_client = GeminiClient(model=prompt.model, prompt=prompt.content, temperature=prompt.temperature)
        response = gemini_client.generate(context=context)

        generated = response.text
        context[prompt.return_variable] = generated

    return generated
