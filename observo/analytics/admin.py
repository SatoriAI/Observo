from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline

from .models import Contact, Survey


class ContactInline(StackedInline):
    model = Contact
    extra = 0
    max_num = 1
    can_delete = True
    fields = ("email", "description", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Survey)
class SurveyAdmin(ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "b_progress",
        "sector",
        "locale",
    )
    list_filter = ("sector", "locale", "created_at")
    search_fields = ("sector", "referrer", "user_agent", "client_ip_hash")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    # Unfold will pretty-format JSON when it's readonly (optionally with Pygments)
    readonly_fields = (
        "created_at",
        "updated_at",
        "answers",
    )

    fields = (
        "created_at",
        "updated_at",
        "answers",
        "sector",
        "locale",
        "user_agent",
        "referrer",
        "client_ip_hash",
        "threshold",
    )

    inlines = (ContactInline,)

    compressed_fields = True  # Compact long forms

    @admin.display(description="B / total")
    def b_progress(self, obj: Survey) -> str:
        return f"{obj.b_count}/{obj.total_questions}"
