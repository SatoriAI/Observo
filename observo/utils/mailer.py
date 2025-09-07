from typing import Any

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from observo import settings


def send_email(
    subject: str, recipients: list[str], cc: list[str] | None, template: str, context: dict[str, Any]
) -> None:
    html_content = render_to_string(template, context)

    email = EmailMultiAlternatives(
        subject=subject, body=html_content, from_email=f"Grant Flow <{settings.EMAIL_HOST_USER}>", to=recipients, cc=cc
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
