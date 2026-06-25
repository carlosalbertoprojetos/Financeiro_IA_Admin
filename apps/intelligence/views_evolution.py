from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.evolution.compatibility.matrix import check_system_compatibility, matrix_as_table
from apps.intelligence.services.evolution.compatibility.query_adapter import adapt_legacy_query, detect_query_version
from apps.intelligence.services.evolution.config import is_safe_mode
from apps.intelligence.services.evolution.feature_flags.flags import all_flags
from apps.intelligence.services.evolution.impact_analyzer import analyze_change_impact
from apps.intelligence.services.evolution.pipeline.orchestrator import run_evolution_pipeline, validate_deployment
from apps.intelligence.services.evolution.rollback.manager import create_snapshot, list_rollback_targets, rollback_to_version
from apps.intelligence.services.evolution.storage import get_evolution_history
from apps.intelligence.services.evolution.versioning.core import version_snapshot


class EvolutionOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "endpoints": {
                "version": "GET /api/evolution/version/",
                "compatibility": "GET /api/evolution/compatibility/?from=1.0.0",
                "impact": "POST /api/evolution/impact/",
                "pipeline": "POST /api/evolution/pipeline/",
                "flags": "GET /api/evolution/flags/",
                "rollback": "POST /api/evolution/rollback/",
                "history": "GET /api/evolution/history/",
                "adapt_query": "POST /api/evolution/impact/ (adapt_query in body)",
            },
            "safe_mode": is_safe_mode(),
            "safe_mode_env": "EOR_SAFE_MODE=true",
        })


class EvolutionVersionView(APIView):
    def get(self, request: Request) -> Response:
        from_version = str(request.query_params.get("from", "1.0.0"))
        snapshot = version_snapshot()
        compat = check_system_compatibility(from_version)
        return Response({
            "versions": snapshot,
            "compatibility": compat,
            "matrix": matrix_as_table(),
            "safe_mode": is_safe_mode(),
        })


class EvolutionImpactView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        if data.get("adapt_query"):
            query = str(data["adapt_query"])
            detected = detect_query_version(query)
            adapted, changes = adapt_legacy_query(query, source_version=detected)
            return Response({
                "detected_version": detected,
                "adapted_query": adapted,
                "adaptations": changes,
            })

        impact = analyze_change_impact(
            change_type=str(data.get("change_type", "upgrade")),
            from_version=str(data.get("from_version", "1.0.0")),
            to_version=data.get("to_version"),
            sample_queries=data.get("sample_queries", []),
            affected_metrics=data.get("affected_metrics", []),
        )
        return Response(impact)


class EvolutionPipelineView(APIView):
    def post(self, request: Request) -> Response:
        data = request.data or {}
        if not data:
            return Response({"error": "Request body required"}, status=status.HTTP_400_BAD_REQUEST)
        result = run_evolution_pipeline(data)
        validation = result["validation"]
        if is_safe_mode() and not validation.get("approved"):
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        return Response(result)


class EvolutionFlagsView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"flags": all_flags(), "safe_mode": is_safe_mode()})


class EvolutionRollbackView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "targets": list_rollback_targets(),
            "current_snapshot": create_snapshot(),
        })

    def post(self, request: Request) -> Response:
        target = str((request.data or {}).get("target_version", ""))
        if not target:
            return Response({"error": "target_version required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            manifest = rollback_to_version(target, initiated_by=str(request.user or "api"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(manifest)


class EvolutionHistoryView(APIView):
    def get(self, request: Request) -> Response:
        limit = int(request.query_params.get("limit", 50))
        return Response({"history": get_evolution_history(limit=limit)})
