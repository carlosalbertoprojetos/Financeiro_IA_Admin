"""Semantic cache and extended coverage tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.models import SemanticEntityCache
from apps.intelligence.services.semantic_layer.cache import get_cached_entity, set_cached_entity
from apps.intelligence.services.semantic_layer.entity_mapper import filter_entities, map_card_to_entity
from apps.intelligence.services.semantic_layer.enrichment import detect_risk_flags
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class SemanticCacheTests(ReportQueryTestMixin, TestCase):
    def test_persist_and_load_entity_cache(self) -> None:
        entity = map_card_to_entity(self.card_aqui, row={"risk_score": 55})
        set_cached_entity("rq_board", entity)
        self.assertTrue(SemanticEntityCache.objects.filter(board_id="rq_board", card_id="card_aqui").exists())
        cached = get_cached_entity("rq_board", "card_aqui")
        assert cached is not None
        self.assertEqual(cached["entity_type"], entity.entity_type.value)

    def test_risk_level_filter(self) -> None:
        low = map_card_to_entity(self.card_done, row={"risk_score": 10})
        high = map_card_to_entity(self.card_aqui, row={"risk_score": 80})
        filtered = filter_entities(
            [low, high],
            {"risk_level": {"op": ">=", "value": "HIGH"}},
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].card_id, "card_aqui")

    def test_risk_flags_detection(self) -> None:
        flags = detect_risk_flags(self.card_aqui, row={"risk_score": 80, "risk_level": "Alto"})
        self.assertIn("overdue", flags)
        self.assertIn("elevated_risk_score", flags)

    def test_entity_status_filter(self) -> None:
        active = map_card_to_entity(self.card_aqui, row={"risk_score": 50})
        done = map_card_to_entity(self.card_done, row={"risk_score": 5})
        filtered = filter_entities(
            [active, done],
            {"entity_status": {"values": ["COMPLETED"]}},
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].card_id, "card_done")

    def test_map_cards_batch(self) -> None:
        from apps.intelligence.services.semantic_layer.entity_mapper import map_cards_to_entities

        entities = map_cards_to_entities(
            [self.card_aqui, self.card_done],
            [{"card_id": "card_aqui", "risk_score": 60}, {"card_id": "card_done", "risk_score": 5}],
        )
        self.assertEqual(len(entities), 2)

    def test_risk_event_from_title(self) -> None:
        self.card_aqui.title = "[OPS] Dependência externa crítica"
        self.card_aqui.due_at = None
        entity = map_card_to_entity(self.card_aqui)
        from apps.intelligence.services.semantic_layer.entities import EntityType

        self.assertEqual(entity.entity_type, EntityType.RISK_EVENT)

    def test_redis_cache_hit(self) -> None:
        from django.core.cache import cache

        entity = map_card_to_entity(self.card_aqui, row={"risk_score": 40})
        set_cached_entity("rq_board", entity)
        cache_key_data = get_cached_entity("rq_board", "card_aqui")
        self.assertIsNotNone(cache_key_data)

    def test_resolve_entities_uses_cache(self) -> None:
        from apps.intelligence.services.semantic_layer.cache import resolve_entities_with_cache
        from apps.intelligence.services.semantic_layer.entity_mapper import map_card_to_entity

        rows = [{"card_id": "card_aqui", "risk_score": 55}]
        first = resolve_entities_with_cache("rq_board", [], map_card_to_entity, [self.card_aqui], rows)
        second = resolve_entities_with_cache("rq_board", [], map_card_to_entity, [self.card_aqui], rows)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].entity_type, second[0].entity_type)
