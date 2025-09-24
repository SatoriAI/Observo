from django.contrib import admin
from unfold.admin import ModelAdmin

from search.models import Website


@admin.register(Website)
class WebsiteAdmin(ModelAdmin):
    list_display = (
        "pk",
        "url",
        "created_at",
    )
    search_fields = ("url",)
    readonly_fields = (
        "url",
        "summary",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("User Data", {"fields": ("url",)}),
        ("Generation Info", {"fields": ("summary",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]
