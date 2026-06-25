from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0006_decisiontracerecord"),
    ]

    operations = [
        migrations.CreateModel(
            name="EvolutionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version_from", models.CharField(max_length=32)),
                ("version_to", models.CharField(max_length=32)),
                ("change_type", models.CharField(db_index=True, max_length=32)),
                ("affected_layers", models.JSONField(default=list)),
                ("risk_assessment", models.JSONField(default=dict)),
                ("status", models.CharField(db_index=True, default="pending", max_length=32)),
                ("details_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "evolution_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["change_type", "-created_at"], name="evolution_log_type_idx"),
                    models.Index(fields=["status", "-created_at"], name="evolution_log_status_idx"),
                ],
            },
        ),
    ]
