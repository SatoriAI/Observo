import logging

import requests
import trafilatura
from celery import shared_task
from charset_normalizer import from_bytes
from rest_framework import status

from search.models import Website
from search.prompts import SUMMARIZE_COMPANY_FROM_HTML
from utils.clients import GeminiClient

logger = logging.getLogger(__name__)


@shared_task(name="scrape_website")
def scrape_website(pk: int) -> None:
    website = Website.objects.get(pk=pk)
    if not website:
        logger.error(f"Website #{pk} not found")
        return

    logger.info(f"Scraping started for: {website.url}")

    # Extract HTML
    try:
        html = get_html(url=website.url)
    except Exception as e:
        logger.error(e)
        return

    # Extract body
    try:
        body = get_body(html=html)
    except Exception as e:
        logger.error(e)
        return

    # Prepare summary
    try:
        summary = get_summary(prompt=SUMMARIZE_COMPANY_FROM_HTML, context={"company": body}, logger=logger)
    except Exception as e:
        logger.error(e)
        return

    website.summary = summary
    website.save()

    logger.info(f"Scraping ended for: {website.url}")

    # Trigger automatic outline preparation once summary is available
    if not website.grantflow:  # If website summary comes from GrantFlow request then outlines are not needed
        try:
            from search.tasks.outline import auto_prepare_outline_for_website

            auto_prepare_outline_for_website.delay(website.pk)
        except Exception as e:
            logger.warning("Failed to enqueue auto outline preparation: %s", e)


def get_html(url: str) -> bytes | None:
    response = requests.get(url)
    if response.status_code == status.HTTP_200_OK:
        return response.content


def get_body(html: bytes) -> str:
    text = trafilatura.extract(
        str(from_bytes(html).best()), include_comments=False, include_tables=False, favor_recall=True
    )
    return text


def get_summary(
    prompt: str,
    context: dict[str, str],
    *,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.2,
    logger: logging.Logger | None = None,
) -> str:
    client = GeminiClient(prompt=prompt, model=model, temperature=temperature, logger=logger)
    response = client.generate(context=context)
    return response.text
