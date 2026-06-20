from django.db import migrations, models


def copy_updated_at_to_last_sync_time(apps, schema_editor):
    IntegrationState = apps.get_model("tip_integrations", "IntegrationState")
    for record in IntegrationState.objects.all():
        if record.last_sync_time is None:
            record.last_sync_time = record.updated_at
            record.save(update_fields=["last_sync_time"])


class Migration(migrations.Migration):
    dependencies = [
        ("tip_integrations", "0004_ingestion_engine"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="IntegrationIngestionState",
            new_name="IntegrationState",
        ),
        migrations.RenameField(
            model_name="integrationstate",
            old_name="cursor",
            new_name="last_sync_cursor",
        ),
        migrations.RemoveConstraint(
            model_name="integrationstate",
            name="unique_ingestion_state_per_connection_provider",
        ),
        migrations.AddField(
            model_name="integrationstate",
            name="last_sync_time",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="integrationstate",
            constraint=models.UniqueConstraint(
                fields=("connection", "provider"),
                name="unique_integration_state_per_connection_provider",
            ),
        ),
        migrations.AddIndex(
            model_name="integrationstate",
            index=models.Index(
                fields=["provider", "last_sync_time"],
                name="tip_integra_provide_8a1f2c_idx",
            ),
        ),
        migrations.RunPython(copy_updated_at_to_last_sync_time, migrations.RunPython.noop),
    ]
