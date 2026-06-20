from django.contrib import admin

from apps.integrations.models import (
    CanonicalTaskRecord,
    IngestionQueueEvent,
    IntegrationConnection,
    IntegrationState,
)


@admin.register(IntegrationConnection)
class IntegrationConnectionAdmin(admin.ModelAdmin):
    list_display = ("name", "provider", "workspace_id", "project_id", "is_active", "last_synced_at")
    list_filter = ("provider", "is_active")
    search_fields = ("name", "project_id", "workspace_id")


@admin.register(CanonicalTaskRecord)
class CanonicalTaskRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "source_provider", "source_id", "status", "connection", "due_date")
    list_filter = ("source_provider", "status")
    search_fields = ("title", "source_id", "project_id")


@admin.register(IntegrationState)
class IntegrationStateAdmin(admin.ModelAdmin):
    list_display = ("provider", "connection", "last_sync_time", "updated_at")
    list_filter = ("provider",)
    search_fields = ("connection__name", "connection__project_id")


@admin.register(IngestionQueueEvent)
class IngestionQueueEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "provider", "connection_id", "processed", "created_at")
    list_filter = ("event_type", "provider", "processed")
    search_fields = ("connection_id",)
