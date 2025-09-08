from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from analytics.actions.notify import notify_selected_contacts
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
        "eager_to_pay",
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
        "eager_to_pay",
        "website",
        "sector",
        "answers",
        "locale",
        "user_agent",
        "referrer",
        "client_ip_hash",
        "created_at",
        "updated_at",
    )

    fieldsets = [
        ("Servey", {"fields": ("eager_to_pay", "website", "sector", "answers")}),
        ("User Data", {"fields": ("locale", "user_agent", "referrer", "client_ip_hash")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    ]

    inlines = (
        ContactInline,
        MeetingInline,
    )

    compressed_fields = True  # Compact long forms


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    actions = [notify_selected_contacts]

    list_display = (
        "email",
        "survey",
        "notified",
        "created_at",
    )
    list_filter = (
        "notified",
        "created_at",
        "survey__sector",
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
        ("Contact Information", {"fields": ("email", "description", "notified")}),
        ("Related Survey", {"fields": ("survey",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Survey Sector")
    def survey_sector(self, obj: Contact) -> str:
        return obj.survey.sector or "N/A"
