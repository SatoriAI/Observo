import logging
import os
import tempfile

from celery import shared_task
from django.conf import settings
from opportunity.models import Opportunity

from search.models import Notification
from utils.mailer import send_email
from utils.pdf_generator import LaTeXPDFGenerator, MarkdownPDFGenerator

logger = logging.getLogger(__name__)


@shared_task(name="send_outline_notification")
def send_outline_notification(pk: int, email: str, source: str) -> None:
    notification = Notification.objects.get(pk=pk)
    grants_list = notification.match.proposals
    grants = []

    match source.lower():
        case "pdf":
            generator = LaTeXPDFGenerator(base_dir=settings.BASE_DIR, logo_relative_path="data/OpenGrant.png")
        case "markdown":
            generator = MarkdownPDFGenerator(base_dir=settings.BASE_DIR, logo_relative_path="data/OpenGrant.png")
        case _:
            raise ValueError("Source must be either PDF or Markdown!")

    tmp_paths = []

    for outline in notification.outlines.all():
        opportunity_id = _filter(grants=grants_list, title=outline.title)
        opportunity = Opportunity.objects.get(pk=opportunity_id)
        grants.append(opportunity)

        tmp_path = os.path.join(tempfile.gettempdir(), f"{opportunity.identifier}.pdf")

        generator.generate(
            title=outline.title,
            text=outline.content,
            output_path=tmp_path,
            opportunity_number=opportunity.identifier,
        )
        tmp_paths.append(tmp_path)

    send_email(
        subject="Your personalised outline",
        recipients=[email],
        cc=None,
        template="email/outline.html",
        attachments=tmp_paths,
        context={"grants": grants},
    )

    notification.set_notified()

    for tmp_path in tmp_paths:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                logger.warning("Failed to remove temporary PDF %s", tmp_path)


def _filter(grants: list[dict], title: str) -> str | None:
    for grant in grants:
        if grant["title"] == title:
            return grant["id"]
