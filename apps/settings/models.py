from django.db import models

from ai.openai_models import DEFAULT_OPENAI_MODEL
from core.models import TimeStampedModel


class WorkspaceConfig(TimeStampedModel):
    """Singleton tenant/workspace configuration."""

    singleton_id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    workspace_name = models.CharField(max_length=255, blank=True, default="")
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    openai_api_key = models.TextField(blank=True, default="")
    openai_model = models.CharField(max_length=64, default=DEFAULT_OPENAI_MODEL)

    class Meta:
        verbose_name = "Workspace configuration"
        constraints = [
            models.CheckConstraint(
                check=models.Q(singleton_id=1),
                name="tip_settings_single_workspace_config",
            ),
        ]

    @classmethod
    def load(cls) -> "WorkspaceConfig":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
