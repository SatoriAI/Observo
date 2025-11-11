from django.contrib import admin
from unfold.admin import ModelAdmin

from opportunity.models import Opportunity


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = (
        "title",
        "head",
        "funding",
        "vectorized",
        "created_at",
    )
    list_filter = ("vectorized",)
    search_fields = (
        "title",
        "head",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "vectorized",
        "source",
        "injection_date",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("Opportunity Info", {"fields": ("id", "identifier", "code", "title", "link")}),
        ("Institutes", {"fields": ("agency", "head")}),
        ("Timeline", {"fields": ("categories", "funding", "awards")}),
        ("Details", {"fields": ("opened", "closed", "archived")}),
        ("Description", {"fields": ("summary", "eligibility", "instruction")}),
        ("System Info", {"fields": ("applications", "success_rate", "vectorized", "source")}),
        ("Timestamps", {"fields": ("injection_date", "created_at", "updated_at")}),
    ]
