from django.contrib import admin

from apps.intelligence.models import (
    CardEnrichment,
    KnowledgeBaseEntry,
    OperationalScoreSnapshot,
    ReportAuditLog,
    TimelineEvent,
)

admin.site.register(TimelineEvent)
admin.site.register(CardEnrichment)
admin.site.register(KnowledgeBaseEntry)
admin.site.register(OperationalScoreSnapshot)
admin.site.register(ReportAuditLog)
