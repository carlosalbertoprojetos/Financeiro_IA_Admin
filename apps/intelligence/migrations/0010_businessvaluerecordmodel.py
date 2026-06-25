from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0009_ole_models"),
    ]

    operations = [
        migrations.CreateModel(
            name="BusinessValueRecordModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_id", models.CharField(db_index=True, max_length=64)),
                ("source_type", models.CharField(db_index=True, max_length=32)),
                ("value_type", models.CharField(db_index=True, max_length=32)),
                ("estimated_cost", models.FloatField(default=0)),
                ("estimated_benefit", models.FloatField(default=0)),
                ("realized_benefit", models.FloatField(default=0)),
                ("avoided_loss", models.FloatField(db_index=True, default=0)),
                ("confidence_score", models.FloatField(default=0)),
                ("currency", models.CharField(default="BRL", max_length=8)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("action_type", models.CharField(blank=True, db_index=True, max_length=32)),
                ("category", models.CharField(blank=True, db_index=True, max_length=64)),
                ("team", models.CharField(blank=True, db_index=True, max_length=128)),
                ("project", models.CharField(blank=True, db_index=True, max_length=255)),
                ("member", models.CharField(blank=True, max_length=255)),
                ("roi_pct", models.FloatField(db_index=True, default=0)),
                ("audit_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "business_value_records",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["action_type", "-created_at"], name="bvr_action_created_idx"),
                    models.Index(fields=["board_id", "category", "-created_at"], name="bvr_board_cat_idx"),
                    models.Index(fields=["team", "-avoided_loss"], name="bvr_team_avoided_idx"),
                ],
            },
        ),
    ]
