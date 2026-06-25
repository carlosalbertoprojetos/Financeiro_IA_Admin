from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0007_evolutionlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decision_id", models.CharField(db_index=True, max_length=64, unique=True)),
                ("source_trace_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("insight", models.TextField()),
                ("priority", models.CharField(db_index=True, default="MEDIUM", max_length=16)),
                ("recommended_actions", models.JSONField(default=list)),
                ("status", models.CharField(db_index=True, default="OPEN", max_length=32)),
                ("owner", models.CharField(default="system", max_length=255)),
                ("context_json", models.JSONField(blank=True, default=dict)),
                ("execution_history", models.JSONField(blank=True, default=list)),
                ("score", models.FloatField(default=0)),
                ("retry_count", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "db_table": "decision_records",
                "ordering": ["-score", "-created_at"],
                "indexes": [
                    models.Index(fields=["board_id", "status", "-score"], name="decision_board_status_idx"),
                    models.Index(fields=["source_trace_id", "-created_at"], name="decision_trace_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ActionExecutionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decision_id", models.CharField(db_index=True, max_length=64)),
                ("action_type", models.CharField(db_index=True, max_length=32)),
                ("execution_mode", models.CharField(default="MANUAL", max_length=16)),
                ("trace_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("status", models.CharField(db_index=True, max_length=32)),
                ("result_json", models.JSONField(blank=True, default=dict)),
                ("user_id", models.CharField(default="system", max_length=255)),
                ("approved_by", models.CharField(blank=True, max_length=255)),
                ("target_card_id", models.CharField(blank=True, db_index=True, max_length=64)),
            ],
            options={
                "db_table": "action_execution_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["decision_id", "-created_at"], name="action_log_decision_idx"),
                    models.Index(fields=["trace_id", "-created_at"], name="action_log_trace_idx"),
                    models.Index(fields=["target_card_id", "-created_at"], name="action_log_card_idx"),
                ],
            },
        ),
    ]
