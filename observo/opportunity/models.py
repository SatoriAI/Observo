import re
import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from utils.models import TimestampedModel


def _clean_text(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s or None


def _fmt_int(n: int | None) -> str | None:
    return f"{n:,}" if n is not None else None


def _line(label: str, value: str | None) -> str | None:
    return f"{label}: {value}" if value else None


class Opportunity(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=255, unique=True, verbose_name="Opportunity Number")
    title = models.CharField(max_length=255, verbose_name="Opportunity Title")
    code = models.CharField(max_length=255, verbose_name="Opportunity Code")
    link = models.URLField(max_length=2048, verbose_name="Opportunity URL", null=True, blank=True)

    agency = models.CharField(max_length=255, verbose_name="Agency Name")
    head = models.CharField(max_length=255, verbose_name="Top Level Agency Name")

    categories = ArrayField(models.CharField(max_length=255), verbose_name="Categories", null=True, blank=True)
    awards = models.PositiveSmallIntegerField(verbose_name="Number of Awards", null=True, blank=True)
    funding = models.PositiveBigIntegerField(verbose_name="Estimated Program Funding", null=True, blank=True)

    opened = models.DateField(verbose_name="Opening Date")
    closed = models.DateField(verbose_name="Closing Date", null=True, blank=True)
    archived = models.DateField(verbose_name="Archiving Date", null=True, blank=True)

    summary = models.TextField(verbose_name="Summary Description", null=True, blank=True)
    eligibility = models.TextField(verbose_name="Applicant Eligibility Description", null=True, blank=True)
    instruction = models.TextField(verbose_name="Submission Instruction", null=True, blank=True)

    applications = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Total applications submitted.")
    success_rate = models.FloatField(null=True, blank=True, help_text="Success rate for applications.")

    vectorized = models.BooleanField(default=False)
    source = models.CharField(max_length=255, null=True, blank=True)
    injection_date = models.DateField(null=True, blank=True, verbose_name="Injection Date")

    def describe(self) -> str:
        parts = []

        # Headline
        title = _clean_text(self.title)
        if title:
            parts.append(title)

        # Agency info
        agency = _clean_text(self.agency)
        head = _clean_text(self.head)
        agency_line = (
            f"{agency} | Top-level: {head}" if agency and head else agency or (f"Top-level: {head}" if head else None)
        )
        parts.append(_line("Agency", agency_line))

        # Categories
        cats = ", ".join([c for c in (self.categories or []) if _clean_text(c)])
        parts.append(_line("Categories", cats if cats else None))

        # Quantities
        parts.append(_line("Expected Awards", _fmt_int(self.awards)))
        parts.append(_line("Estimated Funding", _fmt_int(self.funding)))

        # Long-form text
        parts.append(_line("Eligibility", _clean_text(self.eligibility)))
        parts.append(_line("Submission Instruction", _clean_text(self.instruction)))
        parts.append(_line("Summary", _clean_text(self.summary)))

        # Optional provenance
        parts.append(_line("Source", _clean_text(self.source)))

        text = "\n".join([p for p in parts if p])
        return re.sub(r"[ \t]+", " ", text).strip()

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Opportunity"
        verbose_name_plural = "Opportunities"
