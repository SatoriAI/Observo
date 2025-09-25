from django.db import models

from utils.models import TimestampedModel


class Website(TimestampedModel):
    url = models.URLField(verbose_name="URL")
    summary = models.TextField(null=True, blank=True)


class Match(TimestampedModel):
    website = models.ForeignKey(
        Website,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    proposals = models.JSONField(default=list)


class Notification(TimestampedModel):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    email = models.EmailField(verbose_name="Email")
