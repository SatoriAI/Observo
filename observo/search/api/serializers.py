import logging

from rest_framework import serializers

from search.models import Match, Notification, Website
from search.tasks import match_proposals, scrape_website

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

    class Meta:
        model = Match
        fields = "__all__"
        read_only_fields = (
            "proposals",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict[str, str]) -> Match:
        match = Match.objects.create(website=validated_data.get("website"))
        match_proposals.delay(match.pk, validated_data["summary"])
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
