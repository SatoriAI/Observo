import logging
import os

from django.apps import apps
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from search.models import ManualOutlineRequest, Notification, NotificationEmailBlock, Website

logger = logging.getLogger(__name__)


def _load_default_outline_html() -> str:
    try:
        app_path = apps.get_app_config("search").path
        template_path = os.path.join(app_path, "templates", "email", "_outline_main_default.html")
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Failed to load default outline template: %s", exc)
        # Fallback to the full default main template content
        return (
            "                <p>Thanks for contacting us through our website! Attached are example grant project outlines for the grant programs you selected on our website. OpenGrant helps entrepreneurs secure R&D grants ($250K–$1.4M) at three times the industry success rate; we look forward to supporting your next R&D initiative.</p>\n\n"
            "                {% if grants %}\n"
            "                    We have prepared for you the outlines of example projects (based on the limited information provided by you) for the following requested grants:\n"
            '                    {% include "email/_grants_list.html" %}\n'
            "                {% endif %}\n\n"
            "                <p>Here's how we can help:</p>\n"
            "                <ul>\n"
            "                    <li>Identify the right grant opportunities for your project.</li>\n"
            "                    <li>Write and submit your Project white paper (10 pages of R&D plans).</li>\n"
            "                    <li>Prepare and submit the Full Proposal (50–60 pages) and handle all compliance requirements.</li>\n"
            "                    <li>Provide a designated grant expert to guide you through the entire process until you receive the funding (including resubmission support).</li>\n"
            "                </ul>\n\n"
            "                <p>All of this is covered by a one time retainer fee of $1049 and 3% success fee (only paid if we win the grant for you). No hidden costs.</p>\n\n"
            "                <p>How about a 20-minute meeting to discuss your Project specifics in one of these slots?</p>\n"
            '                <a href="{{ calendly_link }}" class="cta-button">Schedule Your Free Consultation</a>\n'
        )


@receiver(post_save, sender=Notification)
def create_default_email_block(sender, instance: Notification, created: bool, **kwargs) -> None:
    if not created:
        return

    # If a block exists already (e.g., manual creation), do nothing
    if NotificationEmailBlock.objects.filter(notification=instance).exists():
        return

    html = _load_default_outline_html()
    try:
        NotificationEmailBlock.objects.create(notification=instance, html=html)
        logger.info("Created default NotificationEmailBlock for Notification #%s", instance.pk)
    except Exception as exc:  # pragma: no cover - creation failure should not block flow
        logger.warning(
            "Failed to create default NotificationEmailBlock for Notification #%s: %s",
            instance.pk,
            exc,
        )


@receiver(post_save, sender=Website)
def sync_website_summary_to_requests(sender, instance: Website, **kwargs) -> None:
    if not instance.summary or not instance.url:
        return
    try:
        updated = (
            ManualOutlineRequest.objects.filter(website_url=instance.url)
            .filter(Q(summary__isnull=True) | Q(summary__exact=""))
            .update(summary=instance.summary)
        )
        if updated:
            logger.info(
                "Synchronized summary from Website #%s to %s ManualOutlineRequest(s).",
                instance.pk,
                updated,
            )
    except Exception as exc:  # pragma: no cover - defensive log
        logger.warning("Failed syncing website summary to requests: %s", exc)
