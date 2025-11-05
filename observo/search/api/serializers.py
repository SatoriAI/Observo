import logging

from rest_framework import serializers

from search.models import Match, Notification, Website
from search.tasks import match_proposals, prepare_outline, scrape_website

logger = logging.getLogger(__name__)


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = "__all__"
        read_only_fields = (
            "summary",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict[str, str]) -> Website:
        website = Website.objects.create(url=validated_data["url"])
        scrape_website.delay(website.pk)
        return website


class MatchSerializer(serializers.ModelSerializer):
    summary = serializers.CharField(write_only=True)
    funding = serializers.BooleanField(write_only=True, default=True, help_text="If True only Grants with funding.")
    limit = serializers.IntegerField(write_only=True, default=3, help_text="Limit the number of matches.")

    class Meta:
        model = Match
        fields = "__all__"
        read_only_fields = (
            "proposals",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict[str, str]) -> Match:
        if not (website := validated_data.get("website")):
            website = Website.objects.create(summary=validated_data["summary"])

        match = Match.objects.create(website=website)
        match_proposals.delay(match.pk, validated_data["summary"], validated_data["funding"], validated_data["limit"])

        return match


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict[str, str]) -> Notification:
        match = validated_data.get("match")
        email = validated_data.get("email")

        # Prefer unifying by website: reuse a single Notification per website when possible
        website = match.website if match else None
        existing = None
        if website:
            existing = Notification.objects.filter(match__website=website).order_by("-created_at").first()

        # Otherwise fall back to upsert by the exact match
        if not existing and match:
            existing = Notification.objects.filter(match=match).first()

        if existing:
            # If a different match was posted and outlines aren't ready, switch to the posted match
            if match and existing.match_id != match.id and not existing.ready:
                existing.match = match
            if email and existing.email != email:
                existing.email = email
            existing.save()
            return existing

        notification = super().create(validated_data)
        prepare_outline.delay(notification.pk)

        return notification
