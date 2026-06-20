from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WorkspaceConfig",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "singleton_id",
                    models.PositiveSmallIntegerField(default=1, primary_key=True, serialize=False),
                ),
                ("workspace_name", models.CharField(blank=True, default="", max_length=255)),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("openai_api_key", models.TextField(blank=True, default="")),
                ("openai_model", models.CharField(default="gpt-4o-mini", max_length=64)),
            ],
            options={
                "verbose_name": "Workspace configuration",
            },
        ),
        migrations.AddConstraint(
            model_name="workspaceconfig",
            constraint=models.CheckConstraint(
                check=models.Q(("singleton_id", 1)),
                name="tip_settings_single_workspace_config",
            ),
        ),
    ]
