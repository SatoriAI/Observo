from django.contrib import admin
from django.db.models import Count
from unfold.admin import ModelAdmin, StackedInline

from search.actions.rerun_generation import rerun_generation
from search.actions.send_outline_action import (
    send_outline_to_client_markdown,
    send_outline_to_owner_markdown,
)
from search.models import (
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

    inlines = [
        MatchInLine,
    ]

    @admin.display(description="Has Matches")
    def has_matches(self, obj: Website) -> bool:
        if hasattr(obj, "matches"):
            return True
        return False


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
        "match",
        "email",
        "ready",
        "notified",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("User Data", {"fields": ("email",)}),
        ("System Info", {"fields": ("match", "owner", "ready", "notified")}),
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
    ]


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
