from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.adapters import load_board_records
from dashboard.services.builders import (
    build_dashboard_bottlenecks,
    build_dashboard_efficiency,
    build_dashboard_overview,
    build_dashboard_productivity,
)


class BoardContextMixin:
    def load_context(self, request) -> tuple[list, list, str] | Response:
        board_id = request.query_params.get("board_id")
        if not board_id:
            return Response({"error": "board_id query parameter is required"}, status=400)

        include_removed = request.query_params.get("include_removed", "false").lower() == "true"
        cards, actions = load_board_records(
            board_trello_id=board_id,
            include_removed=include_removed,
            reference_time=timezone.now(),
        )
        return cards, actions, board_id


class DashboardOverviewView(BoardContextMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        payload = build_dashboard_overview(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
            throughput_period=request.query_params.get("period", "day"),
        )
        return Response(payload)


class DashboardProductivityView(BoardContextMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        payload = build_dashboard_productivity(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
            throughput_period=request.query_params.get("period", "day"),
        )
        return Response(payload)


class DashboardEfficiencyView(BoardContextMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        payload = build_dashboard_efficiency(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
        )
        return Response(payload)


class DashboardBottlenecksView(BoardContextMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        kwargs = {
            "board_id": board_id,
            "reference_time": timezone.now(),
        }
        aging_threshold = request.query_params.get("aging_threshold_hours")
        if aging_threshold is not None:
            kwargs["aging_threshold_hours"] = float(aging_threshold)

        payload = build_dashboard_bottlenecks(cards, actions, **kwargs)
        return Response(payload)
