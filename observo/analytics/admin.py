from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from analytics.models import Contact, Meeting, Survey


class ContactInline(StackedInline):
    model = Contact
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = (
        "email",
        "description",
        "created_at",
    )


class MeetingInline(StackedInline):
    model = Meeting
    extra = 0
    max_num = 1
    can_delete = False
    fields = (
        "appeared",
        "email",
        "fullname",
        "timezone",
        "start",
        "finish",
        "name",
    )
    readonly_fields = (
        "email",
        "fullname",
        "timezone",
        "start",
        "finish",
        "name",
        "created_at",
    )


@admin.register(Survey)
class SurveyAdmin(ModelAdmin):
    list_display = (
        "created_at",
        "sector",
        "locale",
        "b_progress",
        "threshold",
    )
    list_filter = (
        "sector",
        "locale",
        "created_at",
    )
    search_fields = ("sector",)
    ordering = ("-created_at",)

    # Unfold will pretty-format JSON when it's readonly (optionally with Pygments)
    readonly_fields = (
        "sector",
        "answers",
        "threshold",
        "locale",
        "user_agent",
        "referrer",
        "client_ip_hash",
        "created_at",
    )

    inlines = (
        ContactInline,
        MeetingInline,
    )

    compressed_fields = True  # Compact long forms

    @admin.display(description="B/total")
    def b_progress(self, obj: Survey) -> str:
        return f"{obj.b_count}/{obj.total_questions}"
