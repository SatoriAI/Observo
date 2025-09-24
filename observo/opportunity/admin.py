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
