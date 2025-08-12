from django.db import models

from analytics.enums import PossibleAnswers


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

    def __str__(self) -> str:
        return f"Contact #{self.pk} left by {self.email}"
