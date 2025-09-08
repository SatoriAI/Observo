from django.db import models

from utils.config import RegexPatterns
from utils.functions import extract_calendly_uuid, extract_path_from_uri


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


class Survey(TimestampedModel):
    answers = models.JSONField(default=dict)
    sector = models.CharField(max_length=160, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    eager_to_pay = models.BooleanField(default=False, verbose_name="Eager To Pay")

    locale = models.CharField(max_length=10, null=True, blank=True)
    geo_location = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    client_ip_hash = models.CharField(max_length=128, null=True, blank=True, verbose_name="Hashed Client's IP")

    def __str__(self) -> str:
        return f"Survey #{self.pk}"


class Contact(TimestampedModel):
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name="contact")

    email = models.EmailField()
    description = models.TextField(null=True, blank=True)

    notified = models.BooleanField(default=False, help_text="Indicates whether the contact has been notified.")

    def __str__(self) -> str:
        return f"Contact #{self.pk} left by {self.email}"


class Meeting(TimestampedModel):
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name="meeting")

    uri = models.URLField()
    invitee_uri = models.URLField()

    # Invitee information
    email = models.EmailField()
    nickname = models.CharField(max_length=128, null=True, blank=True)
    firstname = models.CharField(max_length=255, null=True, blank=True)
    lastname = models.CharField(max_length=255, null=True, blank=True)
    timezone = models.CharField(max_length=255, null=True, blank=True)

    # Meeting information
    start = models.DateTimeField()
    finish = models.DateTimeField()
    name = models.CharField(max_length=255, null=True, blank=True)

    appeared = models.BooleanField(default=False, help_text="Indicates whether the customer showed up for the meeting.")

    @property
    def identifier(self) -> str:
        return extract_calendly_uuid(
            pattern=RegexPatterns.CALENDLY_URI_PATTERN.value, string=extract_path_from_uri(uri=self.uri), group="event"
        )

    @property
    def fullname(self) -> str:
        if self.firstname:
            lastname = self.lastname or ""
            return f"{self.firstname} {lastname}".strip()
        return self.nickname

    def __str__(self) -> str:
        return f"Meeting #{self.pk} with {self.email}"
