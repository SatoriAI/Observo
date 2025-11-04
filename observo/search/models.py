from logging import Logger
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from utils.clients import GeminiClient
from utils.models import TimestampedModel


class Website(TimestampedModel):
    url = models.URLField(null=True, blank=True, verbose_name="URL")
    summary = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.url or "Empty URL"


class Match(TimestampedModel):
    website = models.ForeignKey(Website, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
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
    opportunity = models.ForeignKey(
        "opportunity.Opportunity", on_delete=models.SET_NULL, null=True, blank=True, related_name="outlines"
    )
    notification = models.ForeignKey(Notification, related_name="outlines", on_delete=models.CASCADE)
    title = models.CharField(max_length=1024, null=True, blank=True)
    content = models.TextField()

    def __str__(self) -> str:
        return f"Prepared Outline #{self.pk} for {self.notification.email}"


class Workflow(TimestampedModel):
    title = models.CharField(max_length=255, default="Workflow")
    problem = models.TextField(help_text="The name of the problem to be solved by this Workflow.")

    def process(self, context: dict[str, Any], logger: Logger) -> str:
        generated = None

        for prompt in self.prompts.all():
            logger.info(f"Processing Prompt {prompt.name} (#{prompt.pk})")

            gemini_client = GeminiClient(model=prompt.model, prompt=prompt.content, temperature=prompt.temperature)
            response = gemini_client.generate(context=context)

            generated = response.text
            context[prompt.return_variable] = generated

        return generated

    def __str__(self) -> str:
        return self.title


class Prompt(TimestampedModel):
    name = models.CharField(max_length=255)
    content = models.TextField()

    model = models.CharField(max_length=128, default="gemini-2.5-pro")
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Controls randomness of generation (0.0 = deterministic, 1.0 = maximum randomness).",
    )

    workflow = models.ForeignKey(Workflow, null=True, blank=True, on_delete=models.CASCADE, related_name="prompts")

    return_variable = models.CharField(
        null=True,
        blank=True,
        max_length=128,
        verbose_name="Variable Name",
        help_text="The name of the variable that stores the return text from the LLM. Workflow scoped.",
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["pk"]
