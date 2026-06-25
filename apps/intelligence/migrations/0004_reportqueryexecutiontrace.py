from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0003_reportquerylog"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportQueryExecutionTrace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("query_raw", models.TextField()),
                ("ast", models.JSONField(blank=True, default=dict)),
                ("query_plan", models.JSONField(blank=True, default=dict)),
                ("optimized_plan", models.JSONField(blank=True, default=dict)),
                ("estimated_cost", models.PositiveSmallIntegerField(default=0)),
                ("actual_cost", models.PositiveSmallIntegerField(default=0)),
                ("execution_time_ms", models.PositiveIntegerField(default=0)),
                ("user_id", models.CharField(db_index=True, default="anonymous", max_length=255)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("cache_hit", models.BooleanField(default=False)),
                ("rejected_by_guard", models.BooleanField(default=False)),
                ("status", models.CharField(db_index=True, default="success", max_length=16)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "db_table": "report_query_execution_trace",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["board_id", "-created_at"], name="rq_trace_board_idx"),
                    models.Index(fields=["user_id", "-created_at"], name="rq_trace_user_idx"),
                    models.Index(fields=["status", "-created_at"], name="rq_trace_status_idx"),
                    models.Index(fields=["rejected_by_guard", "-created_at"], name="rq_trace_guard_idx"),
                ],
            },
        ),
    ]
