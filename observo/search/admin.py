from django.contrib import admin
from unfold.admin import ModelAdmin

from search.models import Match, Notification, Website


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


@admin.register(Match)
class MatchAdmin(ModelAdmin):
    list_display = (
        "pk",
        "website",
        "created_at",
    )
    search_fields = ("summary",)
    readonly_fields = (
        "website",
        "proposals",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("Generation Info", {"fields": ("proposals",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = (
        "email",
        "created_at",
    )
    search_fields = ("email",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = [
        ("User Data", {"fields": ("email",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]
