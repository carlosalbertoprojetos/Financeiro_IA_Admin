"""Report Query Engine — segmented report generation from combined filters."""

from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload

__all__ = ["ReportQueryPayload", "execute_report_query"]
