from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intelligence.services.organizational_learning.knowledge_graph.graph import build_knowledge_graph
from apps.intelligence.services.organizational_learning.maturity.index import compute_eor_maturity_index
from apps.intelligence.services.organizational_learning.memory.storage import get_memory_history
from apps.intelligence.services.organizational_learning.patterns.analyzer import analyze_action_patterns, get_action_historical_stats
from apps.intelligence.services.organizational_learning.pipeline import build_executive_learning_dashboard
from apps.intelligence.services.organizational_learning.playbooks.engine import generate_playbooks


class LearningOverviewView(APIView):
    def get(self, request: Request) -> Response:
        return Response({
            "endpoints": {
                "dashboard": "GET /api/learning/dashboard/",
                "patterns": "GET /api/learning/patterns/",
                "playbooks": "GET /api/learning/playbooks/",
                "knowledge_graph": "GET /api/learning/knowledge-graph/",
                "memory": "GET /api/learning/memory/",
                "maturity": "GET /api/learning/maturity/",
                "action_stats": "GET /api/learning/actions/{action_type}/",
            },
        })


class LearningDashboardView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        return Response(build_executive_learning_dashboard(board_id=board_id))


class LearningPatternsView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        return Response(analyze_action_patterns(board_id=board_id))


class LearningPlaybooksView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        min_sample = int(request.query_params.get("min_sample", 2))
        return Response({"playbooks": generate_playbooks(board_id=board_id, min_sample_size=min_sample)})


class LearningKnowledgeGraphView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        limit = int(request.query_params.get("limit", 100))
        return Response(build_knowledge_graph(board_id=board_id, limit=limit))


class LearningMemoryView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        limit = int(request.query_params.get("limit", 50))
        return Response({"memory": get_memory_history(board_id=board_id, limit=limit)})


class LearningMaturityView(APIView):
    def get(self, request: Request) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        return Response(compute_eor_maturity_index(board_id=board_id))


class ActionHistoricalStatsView(APIView):
    def get(self, request: Request, action_type: str) -> Response:
        board_id = str(request.query_params.get("board_id", ""))
        category = str(request.query_params.get("category", ""))
        return Response(get_action_historical_stats(action_type, category=category, board_id=board_id))
