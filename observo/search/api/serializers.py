import logging

from rest_framework import serializers

from search.models import Website
from search.tasks import scrape_website

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
