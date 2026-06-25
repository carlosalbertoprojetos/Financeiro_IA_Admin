from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0008_decisionrecord_actionexecutionlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionEffectivenessRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decision_id", models.CharField(db_index=True, max_length=64)),
                ("action_type", models.CharField(db_index=True, max_length=32)),
                ("risk_before", models.FloatField(default=0)),
                ("risk_after", models.FloatField(default=0)),
                ("sla_before", models.FloatField(default=0)),
                ("sla_after", models.FloatField(default=0)),
                ("execution_time", models.PositiveIntegerField(default=0)),
                ("outcome_score", models.FloatField(default=0)),
                ("effectiveness_score", models.FloatField(db_index=True, default=0)),
                ("outcome_label", models.CharField(db_index=True, default="NEUTRAL", max_length=32)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("category", models.CharField(blank=True, db_index=True, max_length=64)),
                ("owner", models.CharField(blank=True, max_length=255)),
                ("context_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "decision_effectiveness",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["action_type", "-effectiveness_score"], name="deff_action_score_idx"),
                    models.Index(fields=["board_id", "category", "-created_at"], name="deff_board_cat_idx"),
                    models.Index(fields=["outcome_label", "-created_at"], name="deff_outcome_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="OrganizationalMemory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("memory_key", models.CharField(db_index=True, max_length=128, unique=True)),
                ("memory_type", models.CharField(db_index=True, max_length=32)),
                ("title", models.CharField(max_length=500)),
                ("content", models.TextField()),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("decision_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("related_action_type", models.CharField(blank=True, db_index=True, max_length=32)),
                ("effectiveness_score", models.FloatField(default=0)),
                ("context_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "organizational_memory",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["memory_type", "-created_at"], name="orgmem_type_idx"),
                    models.Index(fields=["board_id", "memory_type"], name="orgmem_board_type_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="PlaybookRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("playbook_id", models.CharField(db_index=True, max_length=128, unique=True)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("category", models.CharField(blank=True, db_index=True, max_length=64)),
                ("condition_text", models.CharField(max_length=500)),
                ("recommended_action", models.CharField(db_index=True, max_length=32)),
                ("effectiveness_pct", models.FloatField(default=0)),
                ("sample_size", models.PositiveIntegerField(default=0)),
                ("playbook_json", models.JSONField(default=dict)),
            ],
            options={
                "db_table": "operational_playbooks",
                "ordering": ["-effectiveness_pct"],
            },
        ),
    ]
