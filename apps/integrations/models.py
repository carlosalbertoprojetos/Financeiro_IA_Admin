from django.db import models

from core.models import TimeStampedModel


class IntegrationConnection(TimeStampedModel):
    """Registered external provider connection."""

    class Provider(models.TextChoices):
        TRELLO = "trello", "Trello"
        JIRA = "jira", "Jira"
        CLICKUP = "clickup", "ClickUp"

    name = models.CharField(max_length=255, blank=True)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="integration_connections",
    )
    provider = models.CharField(max_length=32, choices=Provider.choices, db_index=True)
    workspace_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="External workspace/organization identifier (Trello organization).",
    )
    project_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="External project/board identifier at the provider.",
    )
    credentials = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["provider", "name"]
        indexes = [
            models.Index(fields=["provider", "project_id"]),
            models.Index(fields=["provider", "workspace_id"]),
        ]

    def __str__(self) -> str:
        label = self.name or self.project_id
        return f"{self.provider}:{label}"

    def mark_synced(self) -> None:
        from django.utils import timezone

        self.last_synced_at = timezone.now()
        self.save(update_fields=["last_synced_at", "updated_at"])


class CanonicalTaskRecord(TimeStampedModel):
    """Persisted canonical task — unified storage for all providers."""

    connection = models.ForeignKey(
        IntegrationConnection,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    source_provider = models.CharField(max_length=32, db_index=True)
    source_id = models.CharField(max_length=128)
    title = models.CharField(max_length=500)
    status = models.CharField(max_length=255, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    project_id = models.CharField(max_length=128, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "source_provider", "source_id"],
                name="unique_canonical_task_per_connection",
            ),
        ]
        indexes = [
            models.Index(fields=["source_provider", "project_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_provider}:{self.source_id} — {self.title[:40]}"


class IntegrationState(TimeStampedModel):
    """Incremental sync state per provider connection."""

    connection = models.ForeignKey(
        IntegrationConnection,
        on_delete=models.CASCADE,
        related_name="integration_states",
    )
    provider = models.CharField(max_length=32, db_index=True)
    last_sync_cursor = models.JSONField(default=dict, blank=True)
    last_sync_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "provider"],
                name="unique_integration_state_per_connection_provider",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "connection"]),
            models.Index(fields=["provider", "last_sync_time"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.connection_id}"


class IngestionQueueEvent(TimeStampedModel):
    """Persisted ingestion queue event."""

    event_type = models.CharField(max_length=64, db_index=True)
    provider = models.CharField(max_length=32, db_index=True)
    connection_id = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "processed", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} ({self.provider})"
