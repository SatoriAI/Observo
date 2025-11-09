import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("opportunity", "0014_alter_opportunity_link"),
        ("search", "0021_website_grantflow"),
    ]

    operations = [
        migrations.CreateModel(
            name="ManualOutlineRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("website_url", models.URLField(blank=True, null=True, verbose_name="Website URL")),
                ("summary", models.TextField(blank=True, null=True)),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, null=True, help_text="Recipient email (defaults if empty)."
                    ),
                ),
                (
                    "opportunity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manual_outline_requests",
                        to="opportunity.opportunity",
                    ),
                ),
            ],
        ),
    ]
