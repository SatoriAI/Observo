from django.db import models

from utils.models import TimestampedModel


class Website(TimestampedModel):
    url = models.URLField(verbose_name="URL")
    summary = models.TextField(null=True, blank=True)
