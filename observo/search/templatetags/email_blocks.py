import logging

from django import template
from django.db import DatabaseError
from django.template import Context
from django.template import Template as DjTemplate
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from search.models import NotificationEmailBlock

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag(takes_context=True)
def render_outline_main(context, notification, grants):
    """
    Render the main section of the outline email.

    Priority:
    1) If the per-notification Email Block is active and has HTML, render it as a Django template
       with helper placeholders available.
    2) Otherwise render the default include template.
    """

    calendly_link = "https://calendly.com/opengrant/federal-grant-consult"

    base_ctx = {
        "notification": notification,
        "grants": grants,
        "calendly_link": calendly_link,
    }

    # Pre-render simple grants list for easier usage in admin-managed HTML
    base_ctx["grants_list_html"] = mark_safe(render_to_string("email/_grants_list.html", {"grants": grants}))

    block = None
    try:
        block = notification.email_block  # OneToOne; may not exist
    except NotificationEmailBlock.DoesNotExist:
        block = None
    except DatabaseError:
        # Table may not exist yet if migrations haven't been applied
        block = None

    # If a block exists, is active and has HTML, use it
    if block and getattr(block, "is_active", False) and getattr(block, "html", "").strip():
        try:
            tmpl = DjTemplate(block.html)
            return mark_safe(tmpl.render(Context(base_ctx)))
        except Exception as exc:
            logger.warning(
                "Failed to render NotificationEmailBlock for Notification #%s: %s",
                getattr(notification, "pk", "?"),
                exc,
            )

    # Fallback reasons logging
    if not block:
        logger.debug(
            "No NotificationEmailBlock found for Notification #%s; using default.",
            getattr(notification, "pk", "?"),
        )
    elif not getattr(block, "is_active", False):
        logger.debug(
            "NotificationEmailBlock is inactive for Notification #%s; using default.",
            getattr(notification, "pk", "?"),
        )
    elif not getattr(block, "html", "").strip():
        logger.debug(
            "NotificationEmailBlock has empty HTML for Notification #%s; using default.",
            getattr(notification, "pk", "?"),
        )

    # Fallback to default
    return mark_safe(render_to_string("email/_outline_main_default.html", base_ctx))
