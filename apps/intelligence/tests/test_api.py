"""API view tests for intelligence endpoints."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from integrations.trello.models import Board, BoardList, Card


class IntelligenceAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.board = Board.objects.create(trello_id="board_api", name="API Board")
        self.board_list = BoardList.objects.create(
            trello_id="list_api", board=self.board, name="Doing", position=1.0
        )
        Card.objects.create(
            trello_id="card_api",
            board=self.board,
            board_list=self.board_list,
            title="Test card",
            status="Doing",
            due_at=timezone.now() + timedelta(days=5),
        )

    def test_overview(self) -> None:
        response = self.client.get("/api/v1/intelligence/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["module"], "intelligence")

    def test_kpis(self) -> None:
        response = self.client.get("/api/v1/intelligence/kpis/?board_id=board_api")
        self.assertEqual(response.status_code, 200)
        self.assertIn("lead_time", response.json())

    def test_bottlenecks(self) -> None:
        response = self.client.get("/api/v1/intelligence/bottlenecks/?board_id=board_api")
        self.assertEqual(response.status_code, 200)

    def test_risks(self) -> None:
        response = self.client.get("/api/v1/intelligence/risks/?board_id=board_api")
        self.assertEqual(response.status_code, 200)

    def test_score(self) -> None:
        response = self.client.get("/api/v1/intelligence/score/?board_id=board_api")
        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.json())

    def test_executive_summary(self) -> None:
        response = self.client.get("/api/v1/intelligence/executive-summary/?board_id=board_api")
        self.assertEqual(response.status_code, 200)

    def test_report(self) -> None:
        response = self.client.get("/api/v1/intelligence/report/?board_id=board_api")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["meta"]["version"], "EOR_V2")

    def test_dashboard_levels(self) -> None:
        for level in ("operational", "management", "director", "ceo"):
            response = self.client.get(
                f"/api/v1/intelligence/dashboard/?board_id=board_api&level={level}"
            )
            self.assertEqual(response.status_code, 200, msg=level)
            self.assertEqual(response.json()["level"], level)

    def test_pipeline(self) -> None:
        response = self.client.post(
            "/api/v1/intelligence/pipeline/",
            {"board_id": "board_api", "use_ai": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("operational_score", response.json())

    def test_enrichment(self) -> None:
        response = self.client.post(
            "/api/v1/intelligence/enrichment/",
            {"board_id": "board_api"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)

    def test_missing_board_id(self) -> None:
        response = self.client.get("/api/v1/intelligence/kpis/")
        self.assertEqual(response.status_code, 400)
