from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.adapters import load_board_records
from analytics.services.builders import build_cards, build_gaps, build_overview, build_team


class BoardMetricsMixin:
    def load_context(self, request) -> tuple[list, list, str] | Response:
        board_trello_id = request.query_params.get("board_id")
        if not board_trello_id:
            return Response({"error": "board_id query parameter is required"}, status=400)

        include_removed = request.query_params.get("include_removed", "false").lower() == "true"
        cards, actions = load_board_records(
            board_trello_id=board_trello_id,
            include_removed=include_removed,
            reference_time=timezone.now(),
        )
        return cards, actions, board_trello_id


class OverviewMetricsView(BoardMetricsMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        period = request.query_params.get("period", "day")
        payload = build_overview(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
            throughput_period=period,
        )
        return Response(payload)


class TeamMetricsView(BoardMetricsMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        payload = build_team(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
        )
        return Response(payload)


class CardsMetricsView(BoardMetricsMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        payload = build_cards(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
        )
        return Response(payload)


class GapsMetricsView(BoardMetricsMixin, APIView):
    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        aging_threshold = request.query_params.get("aging_threshold_hours")
        kwargs = {
            "board_id": board_id,
            "reference_time": timezone.now(),
        }
        if aging_threshold is not None:
            kwargs["aging_threshold_hours"] = float(aging_threshold)

        payload = build_gaps(cards, actions, **kwargs)
        return Response(payload)


class MetricsView(BoardMetricsMixin, APIView):
    """Legacy aggregate endpoint."""

    def get(self, request):
        context = self.load_context(request)
        if isinstance(context, Response):
            return context

        cards, actions, board_id = context
        period = request.query_params.get("period", "day")
        payload = build_overview(
            cards,
            actions,
            board_id=board_id,
            reference_time=timezone.now(),
            throughput_period=period,
        )
        return Response(payload)
