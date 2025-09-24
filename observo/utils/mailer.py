import json
import logging
from dataclasses import dataclass
from typing import Any

import requests
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import status

from observo import settings

logger = logging.getLogger(__name__)


@dataclass
class MailSendResult:
    success: bool
    provider: str
    message: str


def _send_via_smtp(subject: str, html_content: str, recipients: list[str], cc: list[str] | None) -> MailSendResult:
    email = EmailMultiAlternatives(
        subject=subject, body=html_content, from_email=f"Grant Flow <{settings.EMAIL_FROM}>", to=recipients, cc=cc
    )
    email.attach_alternative(html_content, "text/html")
    sent = email.send()
    return MailSendResult(success=bool(sent), provider="smtp", message=f"SMTP send returned {sent}")


def _send_via_resend(subject: str, html_content: str, recipients: list[str], cc: list[str] | None) -> MailSendResult:
    api_key = getattr(settings, "RESEND_API_KEY", None)
    if not api_key:
        return MailSendResult(success=False, provider="resend", message="Missing RESEND_API_KEY")

    payload = {
        "from": settings.EMAIL_FROM,
        "to": recipients,
        "subject": subject,
        "html": html_content,
    }
    if cc:
        payload["cc"] = cc

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            data=json.dumps(payload),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
        )
    except requests.RequestException as exc:
        return MailSendResult(success=False, provider="resend", message=f"HTTP error: {exc}")

    if status.HTTP_200_OK <= resp.status_code < status.HTTP_300_MULTIPLE_CHOICES:
        return MailSendResult(success=True, provider="resend", message="Resend accepted message")
    return MailSendResult(success=False, provider="resend", message=f"Resend error {resp.status_code}: {resp.text}")


def send_email(
    subject: str, recipients: list[str], cc: list[str] | None, template: str, context: dict[str, Any]
) -> None:
    html_content = render_to_string(template, context)

    # Prefer HTTP API to avoid outbound SMTP blocks on some hosts
    if getattr(settings, "RESEND_API_KEY", None):
        result = _send_via_resend(subject, html_content, recipients, cc)
        logger.info("Email send via %s: %s", result.provider, result.message)
        if result.success:
            return
        # fall back to SMTP if HTTP failed
        logger.warning("Falling back to SMTP after Resend failure: %s", result.message)

    # SMTP path (may fail on restricted hosts)
    result = _send_via_smtp(subject, html_content, recipients, cc)
    if not result.success:
        logger.error("SMTP send failed: %s", result.message)
        raise RuntimeError("Failed to send email")
