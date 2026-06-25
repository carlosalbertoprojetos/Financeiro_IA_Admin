from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tip_intelligence", "0004_reportqueryexecutiontrace"),
    ]

    operations = [
        migrations.CreateModel(
            name="SemanticEntityCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("board_id", models.CharField(db_index=True, max_length=64)),
                ("card_id", models.CharField(db_index=True, max_length=64)),
                ("entity_type", models.CharField(db_index=True, max_length=32)),
                ("category", models.CharField(blank=True, max_length=64)),
                ("classification", models.CharField(blank=True, max_length=64)),
                ("entity_data", models.JSONField(default=dict)),
            ],
            options={
                "db_table": "semantic_entity_cache",
                "ordering": ["-updated_at"],
                "indexes": [
                    models.Index(fields=["board_id", "entity_type"], name="semantic_cache_type_idx"),
                    models.Index(fields=["board_id", "category"], name="semantic_cache_cat_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("board_id", "card_id"), name="unique_semantic_entity_per_card"),
                ],
            },
        ),
    ]
