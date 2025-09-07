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


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = (
        "email",
        "survey",
        "notified",
        "created_at",
        "survey_b_progress",
        "survey_sector",
    )
    list_filter = (
        "notified",
        "created_at",
        "survey__sector",
        "survey__locale",
    )
    search_fields = (
        "email",
        "description",
        "survey__sector",
    )
    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Contact Information", {
            "fields": ("email", "description", "notified")
        }),
        ("Related Survey", {
            "fields": ("survey",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Survey Progress")
    def survey_b_progress(self, obj: Contact) -> str:
        return f"{obj.survey.b_count}/{obj.survey.total_questions}"

    @admin.display(description="Survey Sector")
    def survey_sector(self, obj: Contact) -> str:
        return obj.survey.sector or "N/A"
