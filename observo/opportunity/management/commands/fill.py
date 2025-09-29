import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from tqdm import tqdm

from opportunity.models import Opportunity


class Command(BaseCommand):
    help = "Populate field in Opportunity model, e.g. applications and success rate"

    def add_arguments(self, parser):
        parser.add_argument("--recalculate", action="store_true", help="Force recalculation for all Opportunities.")
        parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bar.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["recalculate"]:
            queryset = Opportunity.objects.all()
        else:
            queryset = Opportunity.objects.filter(Q(applications__isnull=True) | Q(success_rate__isnull=True))
        self.stdout.write(f"{queryset.count()} Opportunities will be populated with `applications` and `success_rate`")

        iterator = queryset if options["no_progress"] else tqdm(queryset, total=queryset.count(), unit="objects")
        for opportunity in iterator:
            applications = random.randint(a=12, b=32)
            success_rate = round(random.randint(a=5, b=9) / applications * 100, 2)  # Value as percentage, e.g. 20
            opportunity.applications = applications
            opportunity.success_rate = success_rate
            opportunity.save()

        self.stdout.write(self.style.SUCCESS("Opportunities populated successfully"))
