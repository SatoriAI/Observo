from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.template.response import TemplateResponse
from opportunity.models import Opportunity

from search.models import Match, Notification
from search.tasks import prepare_single_outline


class ManualOutlineForm(forms.Form):
    # Filter: title only (as requested)
    title = forms.CharField(required=False, label="Title contains")

    # Selection
    opportunity = forms.ModelChoiceField(
        queryset=Opportunity.objects.all().order_by("-created_at")[:50],
        required=True,
        label="Opportunity",
        help_text="Select the specific Opportunity to generate an outline for.",
    )


def _filtered_opportunities(cleaned_data: dict) -> "Opportunity.objects":
    qs = Opportunity.objects.all()
    title = cleaned_data.get("title")
    if title:
        qs = qs.filter(title__icontains=title)
    return qs.order_by("-created_at")[:200]


@admin.action(description="Generate Outline for selected Opportunity…")
def generate_single_outline_for_website(model_admin, request, queryset):
    if queryset.count() != 1:
        model_admin.message_user(request, "Please select exactly one Website.", level=messages.WARNING)
        return

    website = queryset.first()

    if request.method == "POST":
        form = ManualOutlineForm(request.POST)

        # Always rebind the opportunity queryset to reflect current filters before validation
        if form.is_valid():
            form.fields["opportunity"].queryset = _filtered_opportunities(form.cleaned_data)

        if request.POST.get("filter"):
            # On filter action, re-render with filtered choices
            if form.is_valid():
                filtered_qs = _filtered_opportunities(form.cleaned_data)
                form.fields["opportunity"].queryset = filtered_qs
                model_admin.message_user(
                    request,
                    f"Filtered to {filtered_qs.count()} opportunities.",
                    level=messages.INFO,
                )
            context = {
                **model_admin.admin_site.each_context(request),
                "title": "Generate Outline for selected Opportunity",
                "website": website,
                "form": form,
                "queryset": queryset,
                "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(request, "admin/website_single_outline.html", context)

        if request.POST.get("apply") and form.is_valid():
            opportunity = form.cleaned_data["opportunity"]

            if not getattr(website, "summary", None):
                model_admin.message_user(
                    request,
                    f"Website #{website.pk} has no summary yet; use 'Fetch summary' first.",
                    level=messages.WARNING,
                )
                return

            match = Match.objects.filter(website=website).order_by("-created_at").first()
            if not match:
                match = Match.objects.create(website=website)

            default_email = getattr(settings, "DEFAULT_NOTIFICATION_EMAIL", "anonymous@open-grant.com")
            notification = Notification.objects.create(match=match, email=default_email)

            prepare_single_outline.delay(notification.pk, str(opportunity.id))
            model_admin.message_user(
                request,
                f"Scheduled outline generation for Website #{website.pk} and Opportunity {opportunity.identifier}.",
            )
            return
    else:
        form = ManualOutlineForm()

    context = {
        **model_admin.admin_site.each_context(request),
        "title": "Generate Outline for selected Opportunity",
        "website": website,
        "form": form,
        "queryset": queryset,
        "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
    }
    return TemplateResponse(request, "admin/website_single_outline.html", context)
