from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0005_semanticentitycache"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionTraceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("trace_id", models.CharField(db_index=True, max_length=64, unique=True)),
                ("query_id", models.CharField(db_index=True, max_length=64)),
                ("query", models.TextField()),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("user_id", models.CharField(db_index=True, default="anonymous", max_length=255)),
                ("execution_time_ms", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(db_index=True, default="success", max_length=16)),
                ("summary", models.JSONField(blank=True, default=dict)),
                ("full_trace_json", models.JSONField(default=dict)),
            ],
            options={
                "db_table": "decision_traces",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["query_id", "-created_at"], name="decision_trace_query_idx"),
                    models.Index(fields=["board_id", "-created_at"], name="decision_trace_board_idx"),
                    models.Index(fields=["status", "-created_at"], name="decision_trace_status_idx"),
                ],
            },
        ),
    ]
