from django.db import models

from utils.models import TimestampedModel


class Website(TimestampedModel):
    url = models.URLField(null=True, blank=True, verbose_name="URL")
    summary = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.url or "Empty URL"


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
    email = models.EmailField()
    owner = models.EmailField(null=True, blank=True, help_text="Debug outline will be sent to this email.")
    ready = models.BooleanField(default=False, help_text="Indicates whether outlines, i.e. one-pagers are prepared.")
    notified = models.BooleanField(default=False)

    def set_ready(self) -> None:
        self.ready = True
        self.save()

    def set_notified(self) -> None:
        self.notified = True
        self.save()


class Outline(TimestampedModel):
    notification = models.ForeignKey(Notification, related_name="outlines", on_delete=models.CASCADE)
    title = models.CharField(max_length=1024, null=True, blank=True)
    content = models.TextField()

    def __str__(self) -> str:
        return f"Prepared Outline #{self.pk} for {self.notification.email}"
