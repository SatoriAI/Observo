import io
import os
import tempfile
import zipfile
from collections.abc import Iterable

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponse
from opportunity.models import Opportunity

from search.enums import OutlineAction
from search.models import Notification, Outline
from search.tasks import send_outline_notification
from utils.pdf_generator import MarkdownPDFGenerator


@admin.action(description="Send Outline to Owners")
def send_outline_to_owner_markdown(model_admin, request, queryset) -> None:
    owners = []
    for notification in queryset:
        if not notification.owner:
            model_admin.message_user(request, "No Owners found!")
            return
        send_outline_notification.delay(notification.pk, notification.owner, OutlineAction.SEND_TO_OWNER)
        owners.append(notification.owner)
    model_admin.message_user(request, f"Successfully send {queryset.count()} Notification(s) to {", ".join(owners)}.")


@admin.action(description="Send Outline to Users")
def send_outline_to_client_markdown(model_admin, request, queryset) -> None:
    emails = []
    for notification in queryset:
        send_outline_notification.delay(notification.pk, notification.email, OutlineAction.SEND_TO_CLIENT)
        emails.append(notification.email)
    model_admin.message_user(request, f"Successfully send {queryset.count()} Notification(s) to {", ".join(emails)}.")


@admin.action(description="Download PDF(s)")
def download_notification_pdfs(model_admin, request, queryset) -> HttpResponse | None:
    """
    Generate PDF(s) for the latest outlines of a single selected Notification and return as a download.
    - If there is one outline, return a single PDF.
    - If there are multiple outlines (up to 3), return a ZIP archive containing all PDFs.
    """
    # Enforce single selection to make the response deterministic
    if queryset.count() != 1:
        model_admin.message_user(request, "Please select exactly one Notification.", level=messages.WARNING)
        return None

    notification: Notification = queryset.first()
    outlines: Iterable[Outline] = notification.outlines.order_by("-created_at")[:3]
    if not outlines:
        model_admin.message_user(request, "No outlines available to generate PDFs.", level=messages.WARNING)
        return None

    # Helper: find Opportunity identifier for naming, mirroring logic in send_outline_notification
    def resolve_identifier_for_outline(o: Outline) -> tuple[str, Opportunity | None]:
        identifier = None
        opportunity_obj: Opportunity | None = None

        # 1) try matching against proposals list by title to get Opportunity by id
        grants_list = getattr(notification.match, "proposals", []) or []
        for grant in grants_list:
            if grant.get("title") == (o.title or "") and grant.get("id"):
                try:
                    opportunity_obj = Opportunity.objects.get(pk=grant["id"])
                    identifier = opportunity_obj.identifier
                except Opportunity.DoesNotExist:
                    opportunity_obj = None
                break

        # 2) use FK if present
        if not identifier and getattr(o, "opportunity_id", None):
            opportunity_obj = o.opportunity
            if opportunity_obj:
                identifier = opportunity_obj.identifier

        # 3) fallback: look up by identifier == outline.title
        if not identifier and (o.title or "").strip():
            found = Opportunity.objects.filter(identifier=o.title).first()
            if found:
                opportunity_obj = found
                identifier = found.identifier

        # 4) final fallback: use outline.title or 'Unknown'
        if not identifier:
            identifier = (o.title or "Unknown").strip() or "Unknown"

        return identifier, opportunity_obj

    # Prepare PDF generator
    generator = MarkdownPDFGenerator(base_dir=settings.BASE_DIR, logo_relative_path="data/OpenGrant.png")

    # If only one outline, stream a single PDF
    outlines_list = list(outlines)
    if len(outlines_list) == 1:
        outline = outlines_list[0]
        identifier, _ = resolve_identifier_for_outline(outline)

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, f"{identifier}.pdf")
            generator.generate(
                title="Outline for " + (outline.title or identifier),
                text=outline.content,
                output_path=pdf_path,
                header_right_text=identifier,
            )
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Outline-{identifier}.pdf"'
        return response

    # Otherwise, package multiple PDFs into a ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        with tempfile.TemporaryDirectory() as tmpdir:
            for outline in outlines_list:
                identifier, _ = resolve_identifier_for_outline(outline)
                pdf_path = os.path.join(tmpdir, f"{identifier}.pdf")
                generator.generate(
                    title="Outline for " + (outline.title or identifier),
                    text=outline.content,
                    output_path=pdf_path,
                    header_right_text=identifier,
                )
                arcname = f"{identifier}.pdf"
                zipf.write(pdf_path, arcname=arcname)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="Outlines-Notification-{notification.pk}.zip"'
    return response
