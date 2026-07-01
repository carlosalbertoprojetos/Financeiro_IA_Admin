from django.db import models

from core.models import TimeStampedModel
from apps.intelligence.domain.events import TimelineEventType


class TimelineEvent(TimeStampedModel):
    """Consolidated operational event history for intelligence pipeline."""

    board = models.ForeignKey(
        "trello.Board",
        on_delete=models.CASCADE,
        related_name="timeline_events",
    )
    card = models.ForeignKey(
        "trello.Card",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="timeline_events",
    )
    source_action = models.ForeignKey(
        "trello.Action",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timeline_events",
    )
    event_type = models.CharField(
        max_length=64,
        choices=TimelineEventType.choices(),
        db_index=True,
    )
    event_timestamp = models.DateTimeField(db_index=True)
    actor = models.CharField(max_length=255, blank=True)
    payload_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-event_timestamp"]
        indexes = [
            models.Index(fields=["board", "-event_timestamp"]),
            models.Index(fields=["card", "-event_timestamp"]),
            models.Index(fields=["board", "event_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_action", "event_type"],
                name="unique_timeline_event_per_action_type",
                condition=models.Q(source_action__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.event_timestamp.isoformat()}"


class CardEnrichment(TimeStampedModel):
    """Persisted executive context for a card."""

    class PriorityLevel(models.TextChoices):
        ALTA = "ALTA", "Alta"
        MEDIA = "MÉDIA", "Média"
        BAIXA = "BAIXA", "Baixa"

    card = models.OneToOneField(
        "trello.Card",
        on_delete=models.CASCADE,
        related_name="enrichment",
    )
    objective = models.TextField(blank=True)
    area = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    project = models.CharField(max_length=255, blank=True)
    client = models.CharField(max_length=255, blank=True)
    priority = models.CharField(
        max_length=16,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIA,
    )
    urgency = models.CharField(max_length=16, default="MÉDIA")
    complexity = models.CharField(max_length=16, default="MÉDIA")
    impact = models.CharField(max_length=16, default="MÉDIA")
    criticality = models.CharField(max_length=16, default="MÉDIA")
    business_value = models.CharField(max_length=16, default="MÉDIA")
    confidence = models.FloatField(default=0.0)
    signals_json = models.JSONField(default=list, blank=True)
    context_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Enrichment: {self.card_id} ({self.priority})"


class KnowledgeBaseEntry(TimeStampedModel):
    """Automatically extracted operational knowledge."""

    class EntryType(models.TextChoices):
        LESSON_LEARNED = "lesson_learned", "Lição aprendida"
        BEST_PRACTICE = "best_practice", "Boa prática"
        RECURRING_PROBLEM = "recurring_problem", "Problema recorrente"
        OPERATIONAL_PATTERN = "operational_pattern", "Padrão operacional"
        ROOT_CAUSE = "root_cause", "Causa raiz"
        RECOMMENDATION = "recommendation", "Recomendação"

    board = models.ForeignKey(
        "trello.Board",
        on_delete=models.CASCADE,
        related_name="knowledge_entries",
    )
    card = models.ForeignKey(
        "trello.Card",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_entries",
    )
    entry_type = models.CharField(max_length=32, choices=EntryType.choices, db_index=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    confidence = models.FloatField(default=0.0)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Knowledge base entries"

    def __str__(self) -> str:
        return f"{self.entry_type}: {self.title[:60]}"


class OperationalScoreSnapshot(TimeStampedModel):
    """Point-in-time EOR Operational Score for a board."""

    class Level(models.TextChoices):
        GREEN = "Verde", "Verde"
        YELLOW = "Amarelo", "Amarelo"
        ORANGE = "Laranja", "Laranja"
        RED = "Vermelho", "Vermelho"

    board = models.ForeignKey(
        "trello.Board",
        on_delete=models.CASCADE,
        related_name="operational_scores",
    )
    score = models.PositiveSmallIntegerField()
    level = models.CharField(max_length=16, choices=Level.choices)
    delivery = models.PositiveSmallIntegerField(default=0)
    deadline = models.PositiveSmallIntegerField(default=0)
    quality = models.PositiveSmallIntegerField(default=0)
    communication = models.PositiveSmallIntegerField(default=0)
    execution = models.PositiveSmallIntegerField(default=0)
    risks = models.PositiveSmallIntegerField(default=0)
    productivity = models.PositiveSmallIntegerField(default=0)
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Score {self.score} ({self.level}) — board {self.board_id}"


class ReportAuditLog(TimeStampedModel):
    """Audit trail for segmented report generation."""

    generated_by = models.CharField(max_length=255, default="anonymous")
    board_id = models.CharField(max_length=64, db_index=True)
    report_type = models.CharField(max_length=32, db_index=True)
    export_format = models.CharField(max_length=16, default="json")
    filters_json = models.JSONField(default=dict)
    matched_cards = models.PositiveIntegerField(default=0)
    processing_ms = models.PositiveIntegerField(default=0)
    cache_hit = models.BooleanField(default=False)
    result_summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board_id", "-created_at"]),
            models.Index(fields=["generated_by", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.report_type} @ {self.board_id} ({self.created_at.isoformat()})"


class ReportQueryLog(TimeStampedModel):
    """Audit trail for EQL query execution."""

    query_raw = models.TextField()
    query_ast = models.JSONField(default=dict, blank=True)
    execution_time_ms = models.PositiveIntegerField(default=0)
    user_id = models.CharField(max_length=255, default="anonymous", db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=16, default="success", db_index=True)
    cache_hit = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "report_query_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board_id", "-created_at"]),
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"EQL {self.status} @ {self.board_id} ({self.execution_time_ms}ms)"


class ReportQueryExecutionTrace(TimeStampedModel):
    """Advanced observability trace for EQL query compilation and execution."""

    query_raw = models.TextField()
    ast = models.JSONField(default=dict, blank=True)
    query_plan = models.JSONField(default=dict, blank=True)
    optimized_plan = models.JSONField(default=dict, blank=True)
    estimated_cost = models.PositiveSmallIntegerField(default=0)
    actual_cost = models.PositiveSmallIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(default=0)
    user_id = models.CharField(max_length=255, default="anonymous", db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    cache_hit = models.BooleanField(default=False)
    rejected_by_guard = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default="success", db_index=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "report_query_execution_trace"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board_id", "-created_at"]),
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["rejected_by_guard", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Trace {self.status} cost={self.estimated_cost} @ {self.board_id}"


class SemanticEntityCache(TimeStampedModel):
    """Cache of inferred business entity classifications."""

    board_id = models.CharField(max_length=64, db_index=True)
    card_id = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=32, db_index=True)
    category = models.CharField(max_length=64, blank=True)
    classification = models.CharField(max_length=64, blank=True)
    entity_data = models.JSONField(default=dict)

    class Meta:
        db_table = "semantic_entity_cache"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["board_id", "card_id"], name="unique_semantic_entity_per_card"),
        ]
        indexes = [
            models.Index(fields=["board_id", "entity_type"]),
            models.Index(fields=["board_id", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.category} @ {self.card_id}"


class DecisionTraceRecord(TimeStampedModel):
    """Full decision trace for observability and audit."""

    trace_id = models.CharField(max_length=64, unique=True, db_index=True)
    query_id = models.CharField(max_length=64, db_index=True)
    query = models.TextField()
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, default="anonymous", db_index=True)
    execution_time_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, default="success", db_index=True)
    summary = models.JSONField(default=dict, blank=True)
    full_trace_json = models.JSONField(default=dict)

    class Meta:
        db_table = "decision_traces"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["query_id", "-created_at"]),
            models.Index(fields=["board_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Trace {self.trace_id} ({self.status})"


class EvolutionLog(TimeStampedModel):
    """Audit log for system evolution and version changes."""

    version_from = models.CharField(max_length=32)
    version_to = models.CharField(max_length=32)
    change_type = models.CharField(max_length=32, db_index=True)
    affected_layers = models.JSONField(default=list)
    risk_assessment = models.JSONField(default=dict)
    status = models.CharField(max_length=32, default="pending", db_index=True)
    details_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "evolution_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["change_type", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.change_type}: {self.version_from} -> {self.version_to} ({self.status})"


class DecisionRecord(TimeStampedModel):
    """Persisted decision object for action queue."""

    decision_id = models.CharField(max_length=64, unique=True, db_index=True)
    source_trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    insight = models.TextField()
    priority = models.CharField(max_length=16, db_index=True, default="MEDIUM")
    recommended_actions = models.JSONField(default=list)
    status = models.CharField(max_length=32, default="OPEN", db_index=True)
    owner = models.CharField(max_length=255, default="system")
    context_json = models.JSONField(default=dict, blank=True)
    execution_history = models.JSONField(default=list, blank=True)
    score = models.FloatField(default=0)
    retry_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "decision_records"
        ordering = ["-score", "-created_at"]
        indexes = [
            models.Index(fields=["board_id", "status", "-score"]),
            models.Index(fields=["source_trace_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Decision {self.decision_id} ({self.priority}/{self.status})"


class ActionExecutionLog(TimeStampedModel):
    """Audit log for executed, blocked, or pending actions."""

    decision_id = models.CharField(max_length=64, db_index=True)
    action_type = models.CharField(max_length=32, db_index=True)
    execution_mode = models.CharField(max_length=16, default="MANUAL")
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=32, db_index=True)
    result_json = models.JSONField(default=dict, blank=True)
    user_id = models.CharField(max_length=255, default="system")
    approved_by = models.CharField(max_length=255, blank=True)
    target_card_id = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        db_table = "action_execution_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["decision_id", "-created_at"]),
            models.Index(fields=["trace_id", "-created_at"]),
            models.Index(fields=["target_card_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action_type} @ {self.decision_id} ({self.status})"


class DecisionEffectivenessRecord(TimeStampedModel):
    """Measured effectiveness of executed decisions — OLE core data."""

    decision_id = models.CharField(max_length=64, db_index=True)
    action_type = models.CharField(max_length=32, db_index=True)
    risk_before = models.FloatField(default=0)
    risk_after = models.FloatField(default=0)
    sla_before = models.FloatField(default=0)
    sla_after = models.FloatField(default=0)
    execution_time = models.PositiveIntegerField(default=0)
    outcome_score = models.FloatField(default=0)
    effectiveness_score = models.FloatField(default=0, db_index=True)
    outcome_label = models.CharField(max_length=32, default="NEUTRAL", db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    category = models.CharField(max_length=64, blank=True, db_index=True)
    owner = models.CharField(max_length=255, blank=True)
    context_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "decision_effectiveness"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action_type", "-effectiveness_score"]),
            models.Index(fields=["board_id", "category", "-created_at"]),
            models.Index(fields=["outcome_label", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action_type} eff={self.effectiveness_score} ({self.outcome_label})"


class OrganizationalMemory(TimeStampedModel):
    """Organizational memory — decisions, results, lessons, playbook candidates."""

    memory_key = models.CharField(max_length=128, unique=True, db_index=True)
    memory_type = models.CharField(max_length=32, db_index=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    decision_id = models.CharField(max_length=64, blank=True, db_index=True)
    related_action_type = models.CharField(max_length=32, blank=True, db_index=True)
    effectiveness_score = models.FloatField(default=0)
    context_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organizational_memory"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["memory_type", "-created_at"]),
            models.Index(fields=["board_id", "memory_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.memory_type}: {self.title[:60]}"


class PlaybookRecord(TimeStampedModel):
    """Evidence-based operational playbooks."""

    playbook_id = models.CharField(max_length=128, unique=True, db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    category = models.CharField(max_length=64, blank=True, db_index=True)
    condition_text = models.CharField(max_length=500)
    recommended_action = models.CharField(max_length=32, db_index=True)
    effectiveness_pct = models.FloatField(default=0)
    sample_size = models.PositiveIntegerField(default=0)
    playbook_json = models.JSONField(default=dict)

    class Meta:
        db_table = "operational_playbooks"
        ordering = ["-effectiveness_pct"]

    def __str__(self) -> str:
        return f"Playbook {self.playbook_id} ({self.effectiveness_pct}%)"


class BusinessValueRecordModel(TimeStampedModel):
    """Auditable financial value record — BVE core persistence."""

    source_id = models.CharField(max_length=64, db_index=True)
    source_type = models.CharField(max_length=32, db_index=True)
    value_type = models.CharField(max_length=32, db_index=True)
    estimated_cost = models.FloatField(default=0)
    estimated_benefit = models.FloatField(default=0)
    realized_benefit = models.FloatField(default=0)
    avoided_loss = models.FloatField(default=0, db_index=True)
    confidence_score = models.FloatField(default=0)
    currency = models.CharField(max_length=8, default="BRL")
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    action_type = models.CharField(max_length=32, blank=True, db_index=True)
    category = models.CharField(max_length=64, blank=True, db_index=True)
    team = models.CharField(max_length=128, blank=True, db_index=True)
    project = models.CharField(max_length=255, blank=True, db_index=True)
    member = models.CharField(max_length=255, blank=True, db_index=True)
    roi_pct = models.FloatField(default=0, db_index=True)
    audit_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "business_value_records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action_type", "-created_at"]),
            models.Index(fields=["board_id", "category", "-created_at"]),
            models.Index(fields=["team", "-avoided_loss"]),
        ]

    def __str__(self) -> str:
        return f"{self.value_type} {self.source_id} ROI={self.roi_pct}%"


class PilotConfig(TimeStampedModel):
    """Active operational pilot scope — one board, one team, human-in-the-loop."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"

    board_id = models.CharField(max_length=64, db_index=True)
    board_name = models.CharField(max_length=255, blank=True)
    team_name = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    config_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "pilot_configs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Pilot {self.board_id} ({self.team_name}/{self.status})"


class PilotCycleRun(TimeStampedModel):
    """Audit log for POCL daily cycle phases and decision streams."""

    class Phase(models.TextChoices):
        STREAM = "STREAM", "Decision stream"
        MORNING = "MORNING", "Morning backlog analysis"
        INTRADAY = "INTRADAY", "Intraday monitoring"
        EOD = "EOD", "End of day report"

    pilot = models.ForeignKey(PilotConfig, on_delete=models.CASCADE, related_name="cycle_runs")
    board_id = models.CharField(max_length=64, db_index=True)
    phase = models.CharField(max_length=16, choices=Phase.choices, db_index=True)
    trigger = models.CharField(max_length=32, default="manual")
    status = models.CharField(max_length=16, default="RUNNING", db_index=True)
    summary_json = models.JSONField(default=dict, blank=True)
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pilot_cycle_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board_id", "phase", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Cycle {self.phase} @ {self.board_id} ({self.status})"


class DecisionFeedbackRecord(TimeStampedModel):
    """Human decision quality feedback — accept, ignore, or modify suggestions."""

    class Disposition(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted suggestion"
        IGNORED = "IGNORED", "Ignored suggestion"
        MODIFIED = "MODIFIED", "Modified before execution"

    decision_id = models.CharField(max_length=64, db_index=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    action_type = models.CharField(max_length=32, blank=True, db_index=True)
    disposition = models.CharField(max_length=16, choices=Disposition.choices, db_index=True)
    operator = models.CharField(max_length=255, default="operator")
    original_action_json = models.JSONField(default=dict, blank=True)
    final_action_json = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    context_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "decision_feedback"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["board_id", "disposition", "-created_at"]),
            models.Index(fields=["decision_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.disposition} @ {self.decision_id}"


class ActionImpactFollowUp(TimeStampedModel):
    """Scheduled real-world impact measurement at 24h / 72h / 7d after action execution."""

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        MEASURED = "MEASURED", "Measured"
        SKIPPED = "SKIPPED", "Skipped"
        FAILED = "FAILED", "Failed"

    decision_id = models.CharField(max_length=64, db_index=True)
    execution_log_id = models.PositiveIntegerField(null=True, blank=True)
    board_id = models.CharField(max_length=64, blank=True, db_index=True)
    card_id = models.CharField(max_length=64, blank=True, db_index=True)
    action_type = models.CharField(max_length=32, db_index=True)
    window_hours = models.PositiveIntegerField(db_index=True)
    scheduled_at = models.DateTimeField(db_index=True)
    measured_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    baseline_json = models.JSONField(default=dict, blank=True)
    measured_json = models.JSONField(default=dict, blank=True)
    impact_json = models.JSONField(default=dict, blank=True)
    estimated_vs_realized_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "action_impact_followups"
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["decision_id", "window_hours"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["decision_id", "window_hours"],
                name="unique_followup_per_decision_window",
            ),
        ]

    def __str__(self) -> str:
        return f"FollowUp {self.decision_id} @ {self.window_hours}h ({self.status})"


class CustomerOnboardingState(TimeStampedModel):
    """Persistent onboarding state used to measure time to first value."""

    class Step(models.TextChoices):
        ACCOUNT = "account", "Account"
        ORGANIZATION = "organization", "Organization"
        TRELLO_TOKEN = "trello_token", "Trello token"
        CONNECTION_TEST = "connection_test", "Connection test"
        INITIAL_SYNC = "initial_sync", "Initial sync"
        BOARD_DISCOVERY = "board_discovery", "Board discovery"
        BOARD_SELECTION = "board_selection", "Board selection"
        INDEXING = "indexing", "Indexing"
        FIRST_ANALYSIS = "first_analysis", "First analysis"
        FIRST_EXECUTIVE_REPORT = "first_executive_report", "First executive report"
        COMPLETED = "completed", "Completed"

    tenant = models.OneToOneField(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="onboarding_state",
    )
    current_step = models.CharField(max_length=64, choices=Step.choices, default=Step.ACCOUNT, db_index=True)
    trello_token_validated = models.BooleanField(default=False)
    boards_discovered = models.JSONField(default=list, blank=True)
    boards_selected = models.JSONField(default=list, blank=True)
    initial_sync_completed = models.BooleanField(default=False)
    first_report_generated = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    errors_json = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "customer_onboarding_state"
        ordering = ["tenant_id"]

    def __str__(self) -> str:
        return f"Onboarding tenant={self.tenant_id} step={self.current_step}"
