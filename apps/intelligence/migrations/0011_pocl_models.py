from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0010_businessvaluerecordmodel"),
    ]

    operations = [
        migrations.CreateModel(
            name="PilotConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("board_id", models.CharField(db_index=True, max_length=64)),
                ("board_name", models.CharField(blank=True, max_length=255)),
                ("team_name", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("ACTIVE", "Active"), ("PAUSED", "Paused"), ("COMPLETED", "Completed")], db_index=True, default="DRAFT", max_length=16)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("config_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "pilot_configs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PilotCycleRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("board_id", models.CharField(db_index=True, max_length=64)),
                ("phase", models.CharField(choices=[("STREAM", "Decision stream"), ("MORNING", "Morning backlog analysis"), ("INTRADAY", "Intraday monitoring"), ("EOD", "End of day report")], db_index=True, max_length=16)),
                ("trigger", models.CharField(default="manual", max_length=32)),
                ("status", models.CharField(db_index=True, default="RUNNING", max_length=16)),
                ("summary_json", models.JSONField(blank=True, default=dict)),
                ("trace_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("pilot", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cycle_runs", to="tip_intelligence.pilotconfig")),
            ],
            options={
                "db_table": "pilot_cycle_runs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DecisionFeedbackRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decision_id", models.CharField(db_index=True, max_length=64)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("action_type", models.CharField(blank=True, db_index=True, max_length=32)),
                ("disposition", models.CharField(choices=[("ACCEPTED", "Accepted suggestion"), ("IGNORED", "Ignored suggestion"), ("MODIFIED", "Modified before execution")], db_index=True, max_length=16)),
                ("operator", models.CharField(default="operator", max_length=255)),
                ("original_action_json", models.JSONField(blank=True, default=dict)),
                ("final_action_json", models.JSONField(blank=True, default=dict)),
                ("reason", models.TextField(blank=True)),
                ("context_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "decision_feedback",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ActionImpactFollowUp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("decision_id", models.CharField(db_index=True, max_length=64)),
                ("execution_log_id", models.PositiveIntegerField(blank=True, null=True)),
                ("board_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("card_id", models.CharField(blank=True, db_index=True, max_length=64)),
                ("action_type", models.CharField(db_index=True, max_length=32)),
                ("window_hours", models.PositiveIntegerField(db_index=True)),
                ("scheduled_at", models.DateTimeField(db_index=True)),
                ("measured_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("SCHEDULED", "Scheduled"), ("MEASURED", "Measured"), ("SKIPPED", "Skipped"), ("FAILED", "Failed")], db_index=True, default="SCHEDULED", max_length=16)),
                ("baseline_json", models.JSONField(blank=True, default=dict)),
                ("measured_json", models.JSONField(blank=True, default=dict)),
                ("impact_json", models.JSONField(blank=True, default=dict)),
                ("estimated_vs_realized_json", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "db_table": "action_impact_followups",
                "ordering": ["scheduled_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pilotcyclerun",
            index=models.Index(fields=["board_id", "phase", "-created_at"], name="pilot_cycle_board_phase_idx"),
        ),
        migrations.AddIndex(
            model_name="decisionfeedbackrecord",
            index=models.Index(fields=["board_id", "disposition", "-created_at"], name="decision_fb_board_disp_idx"),
        ),
        migrations.AddIndex(
            model_name="decisionfeedbackrecord",
            index=models.Index(fields=["decision_id", "-created_at"], name="decision_fb_decision_idx"),
        ),
        migrations.AddIndex(
            model_name="actionimpactfollowup",
            index=models.Index(fields=["status", "scheduled_at"], name="followup_status_sched_idx"),
        ),
        migrations.AddIndex(
            model_name="actionimpactfollowup",
            index=models.Index(fields=["decision_id", "window_hours"], name="followup_decision_window_idx"),
        ),
        migrations.AddConstraint(
            model_name="actionimpactfollowup",
            constraint=models.UniqueConstraint(fields=("decision_id", "window_hours"), name="unique_followup_per_decision_window"),
        ),
    ]
