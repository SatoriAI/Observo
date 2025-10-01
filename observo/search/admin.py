from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from search.actions.send_outline_action import send_outline_to_email, send_outline_to_owner
from search.models import Match, Notification, Outline, Website


class OutlineInLine(StackedInline):
    model = Outline
    fields = (
        "title",
        "content",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "title",
        "created_at",
        "updated_at",
    )
    extra = 0


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
        "owner",
        "ready",
        "notified",
        "created_at",
    )
    list_filter = ("notified",)
    search_fields = ("email",)
    readonly_fields = (
        "ready",
        "notified",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("User Data", {"fields": ("email",)}),
        ("System Info", {"fields": ("owner", "ready", "notified")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    inlines = [
        OutlineInLine,
    ]
    actions = [
        send_outline_to_email,
        send_outline_to_owner,
    ]
