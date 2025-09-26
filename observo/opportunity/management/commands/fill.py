import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from tqdm import tqdm

from opportunity.models import Opportunity


class Command(BaseCommand):
    help = "Populate field in Opportunity model, e.g. applications and success rate"

    def add_arguments(self, parser):
        parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bar.")

    @transaction.atomic
    def handle(self, *args, **options):
        queryset = Opportunity.objects.filter(Q(applications__isnull=True) | Q(success_rate__isnull=True))
        self.stdout.write("%s Opportunities will be populated with `applications` and `success_rate`", queryset.count)

        iterator = queryset if options["no_progress"] else tqdm(queryset, total=len(queryset.count), unit="objects")
        for opportunity in iterator:
            applications = random.randint(a=10, b=25)
            success_rate = random.randint(a=3, b=5) / applications
            opportunity.applications = applications
            opportunity.success_rate = success_rate
            opportunity.save()

        self.stdout.write(self.style.SUCCESS("Opportunities populated successfully"))
