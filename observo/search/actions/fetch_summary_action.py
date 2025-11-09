from django.contrib import admin

from search.tasks import scrape_website


@admin.action(description="Fetch summary from URL")
def fetch_summary_for_website(model_admin, request, queryset) -> None:
    scheduled = 0
    for website in queryset:
        if not getattr(website, "url", None):
            model_admin.message_user(request, f"Website #{website.pk} has no URL; cannot fetch summary.")
            continue
        scrape_website.delay(website.pk)
        scheduled += 1
    model_admin.message_user(request, f"Scheduled summary fetch for {scheduled} Website(s).")
