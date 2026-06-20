from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.integrations.core.ingestion_state import IngestionCursor
from apps.integrations.models import IntegrationConnection
from apps.integrations.trello.incremental import (
    IncrementalCursorSnapshot,
    build_next_cursor,
    filter_changed_cards,
)


class TrelloIncrementalFilterTests(TestCase):
    def _cards(self):
        return [
            {
                "id": "c1",
                "idList": "l1",
                "dateLastActivity": "2026-06-01T10:00:00.000Z",
            },
            {
                "id": "c2",
                "idList": "l2",
                "dateLastActivity": "2026-06-19T10:00:00.000Z",
            },
            {
                "id": "c3",
                "idList": "l1",
                "dateLastActivity": "2026-06-01T08:00:00.000Z",
            },
        ]

    def test_initial_sync_returns_all_cards(self):
        snapshot = IncrementalCursorSnapshot(updated_since=None, card_list_map={})
        changed, stats, mode = filter_changed_cards(self._cards(), snapshot=snapshot)

        self.assertEqual(mode, "initial")
        self.assertEqual(len(changed), 3)
        self.assertEqual(stats.created, 3)

    def test_detects_updated_cards_by_activity(self):
        snapshot = IncrementalCursorSnapshot.from_state(
            IngestionCursor(
                provider="trello",
                connection_id="1",
                cursor={
                    "updated_since": "2026-06-18T00:00:00+00:00",
                    "card_list_map": {"c1": "l1", "c2": "l2", "c3": "l1"},
                },
            )
        )
        changed, stats, mode = filter_changed_cards(self._cards(), snapshot=snapshot)

        self.assertEqual(mode, "incremental")
        self.assertEqual([card["id"] for card in changed], ["c2"])
        self.assertEqual(stats.updated, 1)

    def test_detects_created_cards(self):
        snapshot = IncrementalCursorSnapshot.from_state(
            IngestionCursor(
                provider="trello",
                connection_id="1",
                cursor={
                    "updated_since": "2026-06-18T00:00:00+00:00",
                    "card_list_map": {"c1": "l1"},
                },
            )
        )
        changed, stats, _ = filter_changed_cards(self._cards(), snapshot=snapshot)

        ids = {card["id"] for card in changed}
        self.assertIn("c2", ids)
        self.assertIn("c3", ids)
        self.assertGreaterEqual(stats.created, 2)

    def test_detects_moved_lists_without_recent_activity(self):
        snapshot = IncrementalCursorSnapshot.from_state(
            IngestionCursor(
                provider="trello",
                connection_id="1",
                cursor={
                    "updated_since": "2026-06-18T00:00:00+00:00",
                    "card_list_map": {"c1": "l1", "c2": "l2", "c3": "l2"},
                },
            )
        )
        changed, stats, _ = filter_changed_cards(self._cards(), snapshot=snapshot)

        self.assertIn({"c3"}, [{card["id"]} for card in changed if card["id"] == "c3"])
        self.assertEqual(stats.moved, 1)

    def test_build_next_cursor_stores_card_list_map(self):
        cursor = build_next_cursor(
            board_id="b1",
            all_cards=self._cards(),
            synced_at="2026-06-19T12:00:00+00:00",
            mode="incremental",
            change_stats=filter_changed_cards(
                self._cards(),
                snapshot=IncrementalCursorSnapshot(updated_since=None),
            )[1],
        )

        self.assertEqual(cursor["board_id"], "b1")
        self.assertEqual(cursor["card_list_map"]["c3"], "l1")
        self.assertIn("updated_since", cursor)


class TrelloAdapterIncrementalTests(TestCase):
    @patch("apps.integrations.trello.adapter.TrelloClient")
    def test_fetch_incremental_returns_changed_cards_only(self, mock_client_cls):
        from apps.integrations.trello.adapter import TrelloAdapter

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.get_board.return_value = {"id": "b1", "name": "Board", "idOrganization": ""}
        mock_client.get_lists.return_value = [{"id": "l1", "name": "Doing"}, {"id": "l2", "name": "Done"}]
        mock_client.get_cards.return_value = [
            {
                "id": "c1",
                "name": "old",
                "idList": "l1",
                "dateLastActivity": "2026-06-01T10:00:00.000Z",
                "labels": [],
            },
            {
                "id": "c2",
                "name": "updated",
                "idList": "l1",
                "dateLastActivity": "2026-06-19T10:00:00.000Z",
                "labels": [],
            },
            {
                "id": "c3",
                "name": "moved",
                "idList": "l2",
                "dateLastActivity": "2026-06-01T08:00:00.000Z",
                "labels": [],
            },
        ]

        connection = IntegrationConnection.objects.create(
            provider="trello",
            project_id="b1",
            credentials={"api_key": "k", "api_token": "t"},
        )
        state = IngestionCursor(
            provider="trello",
            connection_id=str(connection.pk),
            cursor={
                "updated_since": "2026-06-18T00:00:00+00:00",
                "card_list_map": {"c1": "l1", "c2": "l1", "c3": "l1"},
            },
        )

        adapter = TrelloAdapter()
        result = adapter.fetch_incremental(state, connection)

        ids = {card["id"] for card in result.payload["cards"]}
        self.assertEqual(ids, {"c2", "c3"})
        self.assertEqual(result.cursor["mode"], "incremental")
        self.assertEqual(result.cursor["changes_last_run"]["updated"], 1)
        self.assertEqual(result.cursor["changes_last_run"]["moved"], 1)
        self.assertEqual(result.cursor["card_list_map"]["c3"], "l2")
