from django.contrib import admin

from search.models import Match, Website


@admin.action(description="Merge two Websites (keep lower ID; move Matches)")
def merge_websites(model_admin, request, queryset) -> None:
    count = queryset.count()
    if count != 2:
        model_admin.message_user(request, "Please select exactly two Website objects to merge.")
        return

    websites = sorted(list(queryset), key=lambda w: w.pk)
    primary: Website = websites[0]  # keep this one
    secondary: Website = websites[1]  # move from this one

    # Move all matches from secondary to primary
    moved = Match.objects.filter(website=secondary).update(website=primary)

    # If primary has no summary but secondary does, copy it over
    if not primary.summary and secondary.summary:
        primary.summary = secondary.summary
        primary.save(update_fields=["summary", "updated_at"])

    model_admin.message_user(
        request,
        f"Merged Websites #{primary.pk} <-> #{secondary.pk}: moved {moved} Match(es).",
    )


