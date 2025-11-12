from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline

from search.actions.fetch_summary_action import fetch_summary_for_website
from search.actions.manual_outline_request_actions import (
    fetch_summary_for_requests,
    generate_outline_for_requests,
)
from search.actions.mark_websites_as_test_action import mark_websites_as_test
from search.actions.merge_websites_action import merge_websites
from search.actions.rerun_generation import rerun_generation
from search.actions.send_outline_action import (
    download_notification_pdfs,
    send_outline_to_client_markdown,
    send_outline_to_owner_markdown,
)
from search.actions.website_manual_outline_action import generate_single_outline_for_website
from search.actions.website_outline_action import (
    create_notification_and_prepare_outline,
)
from search.models import (
    ManualOutlineRequest,
    Match,
    Notification,
    NotificationEmailBlock,
    Outline,
    Prompt,
    Website,
    Workflow,
)


class MatchInLine(StackedInline):
    model = Match
    fields = ("proposals",)
    readonly_fields = ("proposals",)
    extra = 0
    can_delete = False


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


class NotificationEmailBlockInline(StackedInline):
    model = NotificationEmailBlock
    fields = (
        "is_active",
        "html",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    extra = 1


class PromptInline(StackedInline):
    model = Prompt
    extra = 0
    show_change_link = True
    autocomplete_fields = ["workflow"]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = [
        ("Prompt", {"fields": ("name", "content")}),
        ("LLM Settings", {"fields": ("model", "temperature")}),
        ("Variables", {"fields": ("return_variable",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]


@admin.register(Website)
class WebsiteAdmin(ModelAdmin):
    list_display = (
        "pk",
        "url",
        "has_matches",
        "has_notification",
        "grantflow",
        "test",
        "created_at",
    )
    list_filter = (
        "test",
        "grantflow",
    )
    search_fields = ("url",)
    readonly_fields = (
        "summary",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("User Data", {"fields": ("url",)}),
        ("Generation Info", {"fields": ("summary",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    inlines = [
        MatchInLine,
    ]

    actions = [
        fetch_summary_for_website,
        generate_single_outline_for_website,
        create_notification_and_prepare_outline,
        merge_websites,
        mark_websites_as_test,
    ]

    @admin.display(description="Has Matches")
    def has_matches(self, obj: Website) -> bool:
        if hasattr(obj, "matches"):
            return True
        return False

    @admin.display(description="Has Notification")
    def has_notification(self, obj: Website) -> bool:
        return Notification.objects.filter(match__website=obj).exists()


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = (
        "email",
        "owner",
        "website",
        "ready",
        "notified",
        "created_at",
    )
    list_filter = ("notified",)
    search_fields = ("email",)
    readonly_fields = (
        "website",
        "email",
        "ready",
        "notified",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("User Data", {"fields": ("email",)}),
        ("System Info", {"fields": ("website", "owner", "ready", "notified")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    inlines = [
        NotificationEmailBlockInline,
        OutlineInLine,
    ]
    actions = [
        rerun_generation,
        send_outline_to_client_markdown,
        send_outline_to_owner_markdown,
        download_notification_pdfs,
    ]

    @admin.display(description="Website", ordering="match__website__url")
    def website(self, obj: Notification) -> str:
        if not getattr(obj, "match", None) or not getattr(obj.match, "website", None):
            return "—"
        website = obj.match.website
        url = reverse("admin:search_website_change", args=[website.pk])
        label = website.url or f"Website #{website.pk}"
        return format_html('<a href="{}">{}</a>', url, label)


@admin.register(Workflow)
class WorkflowAdmin(ModelAdmin):
    list_display = ("title", "short_problem", "prompts_count", "created_at")
    search_fields = ("title", "problem")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = [
        ("Workflow", {"fields": ("title", "problem")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    inlines = [
        PromptInline,
    ]

    @admin.display(description="Prompts", ordering="prompts_count")
    def prompts_count(self, obj: Workflow) -> int:
        return getattr(obj, "prompts_count", 0)

    @admin.display(description="Problem")
    def short_problem(self, obj: Workflow) -> str:
        if not obj.problem:
            return "—"
        s = str(obj.problem)
        return s if len(s) <= 80 else s[:77] + "…"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(prompts_count=Count("prompts"))


@admin.register(ManualOutlineRequest)
class ManualOutlineRequestAdmin(ModelAdmin):
    list_display = ("website_url", "opportunity", "email", "created_at")
    search_fields = ("website_url", "opportunity__title", "opportunity__identifier")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["opportunity"]

    fieldsets = [
        ("Input", {"fields": ("website_url", "summary", "opportunity")}),
        ("Delivery", {"fields": ("email",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    actions = [
        fetch_summary_for_requests,
        generate_outline_for_requests,
    ]
