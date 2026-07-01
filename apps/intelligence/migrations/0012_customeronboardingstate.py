# Generated for SaaS production blockers removal.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_initial"),
        ("tip_intelligence", "0011_pocl_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerOnboardingState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "current_step",
                    models.CharField(
                        choices=[
                            ("account", "Account"),
                            ("organization", "Organization"),
                            ("trello_token", "Trello token"),
                            ("connection_test", "Connection test"),
                            ("initial_sync", "Initial sync"),
                            ("board_discovery", "Board discovery"),
                            ("board_selection", "Board selection"),
                            ("indexing", "Indexing"),
                            ("first_analysis", "First analysis"),
                            ("first_executive_report", "First executive report"),
                            ("completed", "Completed"),
                        ],
                        db_index=True,
                        default="account",
                        max_length=64,
                    ),
                ),
                ("trello_token_validated", models.BooleanField(default=False)),
                ("boards_discovered", models.JSONField(blank=True, default=list)),
                ("boards_selected", models.JSONField(blank=True, default=list)),
                ("initial_sync_completed", models.BooleanField(default=False)),
                ("first_report_generated", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("errors_json", models.JSONField(blank=True, default=list)),
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="onboarding_state",
                        to="core.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "customer_onboarding_state",
                "ordering": ["tenant_id"],
            },
        ),
    ]
