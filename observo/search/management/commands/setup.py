import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tqdm import tqdm

from search.models import Prompt, Workflow

VARIABLE_MAPPING = {
    "{{ name }}": "the startup",
    "{{ all_insights }}": "{summary}",
    "{{ grantor_funding_blueprint }}": "{opportunity}",
    "{{ short_description_of_innovation_product }}": "{summary}",
}


def _build_variable_lookup(mapping: dict[str, str]) -> dict[str, str]:
    pattern = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
    lookup: dict[str, str] = {}
    for key, value in mapping.items():
        match = pattern.fullmatch(key)
        if match:
            var_name = match.group(1).strip()
            lookup[var_name] = value
    return lookup


def transform_prompt_content(raw_content: str, mapping_lookup: dict[str, str]) -> str:
    pattern = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")

    def replacer(match: re.Match[str]) -> str:
        variable_name = match.group(1).strip()
        if variable_name in mapping_lookup:
            return mapping_lookup[variable_name]
        # Default: convert {{ x }} -> {x}
        return "{" + variable_name + "}"

    return pattern.sub(replacer, raw_content)


class Command(BaseCommand):
    help = "Populate prompts for specific workflow"

    def add_arguments(self, parser):
        parser.add_argument("workflow_id", type=int, help="Primary key of the Workflow to attach prompts to.")
        parser.add_argument(
            "--file",
            "-f",
            dest="file_path",
            default=str(Path(settings.BASE_DIR) / "data" / "prompts.json"),
            help="Path to prompts.json file (defaults to observo/data/prompts.json).",
        )
        parser.add_argument("--replace", action="store_true", help="Replace existing prompts for the workflow.")
        parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bar.")

    @transaction.atomic
    def handle(self, *args, **options):
        workflow_id: int = options["workflow_id"]
        file_path = Path(options["file_path"]).resolve()
        replace_existing: bool = options["replace"]
        show_progress: bool = not options["no_progress"]

        try:
            workflow = Workflow.objects.get(pk=workflow_id)
        except Workflow.DoesNotExist as exc:
            raise CommandError(f"Workflow with id={workflow_id} does not exist.") from exc

        if not file_path.exists():
            raise CommandError(f"Prompts file not found at: {file_path}")

        with file_path.open("r", encoding="utf-8") as fp:
            try:
                prompts_spec = json.load(fp)
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid JSON in {file_path}: {exc}") from exc

        if not isinstance(prompts_spec, list):
            raise CommandError("prompts.json must contain a top-level JSON array")

        if replace_existing:
            deleted_count, _ = workflow.prompts.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted_count} existing prompts for workflow #{workflow.pk}")
            )

        mapping_lookup = _build_variable_lookup(VARIABLE_MAPPING)

        # Sort by 'order' if present to preserve intended execution sequence
        try:
            prompts_spec.sort(key=lambda item: item.get("order", 0))
        except Exception:
            pass

        iterator = prompts_spec
        if show_progress:
            iterator = tqdm(prompts_spec, total=len(prompts_spec), unit="prompts")

        created_count = 0
        for item in iterator:
            raw_content: str = item.get("content", "")
            if not raw_content:
                continue

            transformed_content = transform_prompt_content(raw_content, mapping_lookup)

            order_value = item.get("order")
            role_value = item.get("role") or item.get("return_variable") or "prompt"
            prompt_name = f"{order_value:02d}-{role_value}" if isinstance(order_value, int) else str(role_value)

            model_name = item.get("model") or "gemini-2.5-pro"
            temperature_value = item.get("temperature")
            temperature_value = 0.7 if temperature_value is None else float(temperature_value)
            return_variable = item.get("return_variable")

            Prompt.objects.create(
                name=prompt_name,
                content=transformed_content,
                model=model_name,
                temperature=temperature_value,
                workflow=workflow,
                return_variable=return_variable,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Prompts ({created_count}) added successfully to Workflow #{workflow.pk}!")
        )
