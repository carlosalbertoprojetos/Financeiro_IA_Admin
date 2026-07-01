from django.db import models

from core.models import TimeStampedModel
from core.tenant_queryset import TenantScopedManager, TenantScopedQuerySet


class Board(TimeStampedModel):
    """Current state of a Trello board (mutable projection)."""

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="trello_boards",
    )
    trello_id = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True)
    closed = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    objects = TenantScopedManager()
    all_objects = models.Manager()

    def __str__(self) -> str:
        return self.name


class BoardList(TimeStampedModel):
    """Current state of a Trello list (mutable projection)."""

    trello_id = models.CharField(max_length=64, unique=True, db_index=True)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="lists",
    )
    name = models.CharField(max_length=255)
    position = models.FloatField(default=0)
    closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class Member(TimeStampedModel):
    """Current state of a Trello member (mutable projection)."""

    trello_id = models.CharField(max_length=64, unique=True, db_index=True)
    username = models.CharField(max_length=255, blank=True)
    full_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["full_name", "username"]

    def __str__(self) -> str:
        return self.full_name or self.username or self.trello_id


class Card(TimeStampedModel):
    """Current state of a Trello card (mutable projection)."""

    trello_id = models.CharField(max_length=64, unique=True, db_index=True)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="cards",
    )
    board_list = models.ForeignKey(
        BoardList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cards",
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=255, blank=True)
    assignees = models.ManyToManyField(
        Member,
        blank=True,
        related_name="cards",
    )
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    labels = models.JSONField(default=list, blank=True)
    url = models.URLField(max_length=500, blank=True)
    position = models.FloatField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    raw_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["position", "title"]
        indexes = [
            models.Index(fields=["board", "status"]),
            models.Index(fields=["board", "is_closed"]),
        ]

    def __str__(self) -> str:
        return self.title


class Action(TimeStampedModel):
    """Immutable Trello event log (event sourcing source)."""

    trello_id = models.CharField(max_length=64, unique=True, db_index=True)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="actions",
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    action_type = models.CharField(max_length=64, db_index=True)
    raw_json = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["board", "action_type"]),
            models.Index(fields=["board", "-occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action_type} @ {self.occurred_at.isoformat()}"


class CardStatusHistory(TimeStampedModel):
    """Append-only status transitions for a card."""

    class Source(models.TextChoices):
        SYNC = "sync", "Sync"
        ACTION = "action", "Action"

    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(max_length=255)
    board_list = models.ForeignKey(
        BoardList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="card_status_history",
    )
    board_list_trello_id = models.CharField(max_length=64, blank=True)
    board_list_name = models.CharField(max_length=255, blank=True)
    effective_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.SYNC)
    source_action = models.ForeignKey(
        Action,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="card_status_changes",
    )

    class Meta:
        ordering = ["-effective_at"]
        indexes = [
            models.Index(fields=["card", "-effective_at"]),
            models.Index(fields=["card", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.card_id}: {self.status} @ {self.effective_at.isoformat()}"


class EntityHistory(TimeStampedModel):
    """Append-only log of entity state revisions (simple event sourcing)."""

    class EntityType(models.TextChoices):
        BOARD = "board", "Board"
        LIST = "list", "List"
        CARD = "card", "Card"
        MEMBER = "member", "Member"

    class Source(models.TextChoices):
        SYNC = "sync", "Sync"
        ACTION = "action", "Action"

    entity_type = models.CharField(max_length=16, choices=EntityType.choices, db_index=True)
    entity_trello_id = models.CharField(max_length=64, db_index=True)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="entity_histories",
    )
    state_json = models.JSONField(default=dict)
    effective_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.SYNC)
    source_action = models.ForeignKey(
        Action,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entity_histories",
    )

    class Meta:
        ordering = ["-effective_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_trello_id", "-effective_at"]),
            models.Index(fields=["board", "-effective_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.entity_trello_id} @ {self.effective_at.isoformat()}"


class Snapshot(TimeStampedModel):
    """Daily point-in-time capture of full board state."""

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    snapshot_date = models.DateField(db_index=True)
    state_json = models.JSONField(default=dict)
    card_count = models.PositiveIntegerField(default=0)
    list_count = models.PositiveIntegerField(default=0)
    member_count = models.PositiveIntegerField(default=0)
    action_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-snapshot_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["board", "snapshot_date"],
                name="unique_board_snapshot_date",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.board.name} @ {self.snapshot_date.isoformat()}"
