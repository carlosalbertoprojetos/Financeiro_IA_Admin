# Generated manually for ReportQueryLog

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0002_reportauditlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportQueryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("query_raw", models.TextField()),
                ("query_ast", models.JSONField(blank=True, default=dict)),
                ("execution_time_ms", models.PositiveIntegerField(default=0)),
                ("user_id", models.CharField(db_index=True, default="anonymous", max_length=255)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("status", models.CharField(db_index=True, default="success", max_length=16)),
                ("cache_hit", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
            ],
            options={
                "db_table": "report_query_logs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["board_id", "-created_at"], name="report_query_board_idx"),
                    models.Index(fields=["user_id", "-created_at"], name="report_query_user_idx"),
                    models.Index(fields=["status", "-created_at"], name="report_query_status_idx"),
                ],
            },
        ),
    ]
