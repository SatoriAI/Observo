from django.db import models

from analytics.enums import PossibleAnswers
from utils.config import RegexPatterns
from utils.functions import extract_calendly_uuid, extract_path_from_uri
from analytics.tasks import notify_contact

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


class Survey(TimestampedModel):
    answers = models.JSONField(default=dict)
    sector = models.CharField(max_length=160, null=True, blank=True)

    threshold = models.PositiveSmallIntegerField(default=0, help_text="The required amount of B answers for call.")

    locale = models.CharField(max_length=10, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    client_ip_hash = models.CharField(max_length=128, null=True, blank=True, verbose_name="Hashed Client's IP")

    @property
    def total_questions(self) -> int:
        return len(self.answers or {})

    @property
    def b_count(self) -> int:
        return sum(1 for answer in self.answers.values() if answer == PossibleAnswers.ANSWER_B)

    def __str__(self) -> str:
        return f"Survey #{self.pk} (b={self.b_count}/{self.total_questions})"


class Contact(TimestampedModel):
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name="contact")

    email = models.EmailField()
    description = models.TextField(null=True, blank=True)

    notified = models.BooleanField(default=False, help_text="Indicates whether the contact has been notified.")

    def __str__(self) -> str:
        return f"Contact #{self.pk} left by {self.email}"

    def notify(self) -> None:
        if not self.notified:
            notify_contact.delay(self.id)
            self.notified = True
            self.save()

    def save(self, *args, **kwargs) -> None:
        self.notify()
        super().save(*args, **kwargs)


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
