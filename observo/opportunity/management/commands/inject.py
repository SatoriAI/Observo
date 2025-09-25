import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from opportunity.models import Opportunity

MODEL_CSV_MAPPING = {
    "id": "opportunity_id",
    "identifier": "opportunity_number",
    "title": "opportunity_title",
    "code": "agency_code",
    "agency": "agency_name",
    "head": "top_level_agency_name",
    "categories": "funding_categories",
    "opened": "post_date",
    "closed": "close_date",
    "instruction": "close_date_description",
    "archived": "archive_date",
    "awards": "expected_number_of_awards",
    "funding": "estimated_total_program_funding",
    "eligibility": "applicant_eligibility_description",
    "summary": "summary_description",
}


class Command(BaseCommand):
    help = "Inject Grants from CSV provided by https://simpler.grants.gov/"

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to CSV provided by https://simpler.grants.gov/.")
        parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bar.")

    @transaction.atomic
    def handle(self, *args, **options):
        data = pd.read_csv(options["path"])
        data.replace({np.nan: None}, inplace=True)

        created, updated = 0, 0

        records = data.to_dict(orient="records")
        iterator = records if options["no_progress"] else tqdm(records, total=len(records), unit="row")

        for row in iterator:
            identifier = row[MODEL_CSV_MAPPING["id"]]

            values = {}
            for model_key, csv_key in MODEL_CSV_MAPPING.items():
                if model_key == "id":
                    continue

                if not model_key == "categories":
                    values[model_key] = row[csv_key]
                else:
                    values[model_key] = row[csv_key].split(";")

                if model_key == "awards" or model_key == "funding":
                    if row[csv_key] is not None:
                        values[model_key] = int(row[csv_key])

            try:
                opportunity, created = Opportunity.objects.update_or_create(id=identifier, **values)
            except Exception:  # pylint: disable=too-broad-exception
                self.stdout.write(self.style.ERROR(f"Failed for {identifier}"))
                return

            opportunity.document = options["path"]
            opportunity.save()

            if created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS("Successfully injected Grants from CSV provided."))
        self.stdout.write(
            self.style.SUCCESS(f"Command updated {updated} and created {created} Grants ({created + updated} total).")
        )
