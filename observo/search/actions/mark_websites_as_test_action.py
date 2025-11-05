from django.contrib import admin


@admin.action(description="Mark selected Websites as Test")
def mark_websites_as_test(model_admin, request, queryset) -> None:
    updated = queryset.update(test=True)
    model_admin.message_user(request, f"Marked {updated} Website(s) as Test.")
