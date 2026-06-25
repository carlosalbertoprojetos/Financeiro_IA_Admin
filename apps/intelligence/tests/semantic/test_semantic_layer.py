"""Business Semantic Layer tests."""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.intelligence.services.semantic_layer.entities import EntityStatus, EntityType
from apps.intelligence.services.semantic_layer.entity_mapper import (
    filter_entities,
    map_card_to_entity,
)
from apps.intelligence.services.semantic_layer.enrichment import classify_operational_intent, detect_work_type
from apps.intelligence.services.semantic_layer.metrics import compute_business_metrics
from apps.intelligence.services.semantic_layer.domain_intelligence import generate_domain_insights
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class EntityMapperTests(ReportQueryTestMixin, TestCase):
    def test_card_to_incident(self) -> None:
        self.card_aqui.title = "[FINANCEIRO] Pagamento fornecedor XPTO atrasado"
        entity = map_card_to_entity(self.card_aqui, row={"risk_score": 65})
        self.assertEqual(entity.entity_type, EntityType.INCIDENT)
        self.assertEqual(entity.category, "FINANCEIRO")
        self.assertIn(entity.severity.value, ("HIGH", "CRITICAL", "MEDIUM"))
        self.assertEqual(entity.status, EntityStatus.DELAYED)

    def test_card_to_delivery(self) -> None:
        entity = map_card_to_entity(self.card_done, row={"risk_score": 10})
        self.assertEqual(entity.entity_type, EntityType.DELIVERY)
        self.assertEqual(entity.status, EntityStatus.COMPLETED)

    def test_filter_by_entity_type(self) -> None:
        incident = map_card_to_entity(self.card_aqui, row={"risk_score": 70})
        delivery = map_card_to_entity(self.card_done)
        filtered = filter_entities(
            [incident, delivery],
            {"entity_type": {"values": ["INCIDENT"]}},
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].entity_type, EntityType.INCIDENT)

    def test_filter_by_category(self) -> None:
        self.card_aqui.title = "[FINANCEIRO] Revisar Contrato"
        entity = map_card_to_entity(self.card_aqui)
        filtered = filter_entities([entity], {"category": "FINANCEIRO"})
        self.assertEqual(len(filtered), 1)


class ClassificationTests(ReportQueryTestMixin, TestCase):
    def test_delay_classified_as_incident(self) -> None:
        self.assertEqual(detect_work_type(self.card_aqui), "INCIDENT")

    def test_completion_classified_as_delivery(self) -> None:
        self.assertEqual(detect_work_type(self.card_done), "DELIVERY")

    def test_incident_intent(self) -> None:
        self.card_aqui.title = "[URGENTE] Pagamento atrasado"
        entity = map_card_to_entity(self.card_aqui)
        intent = classify_operational_intent(self.card_aqui, entity.entity_type)
        self.assertIn(intent, ("escalation", "incident_response"))


class BusinessMetricsTests(ReportQueryTestMixin, TestCase):
    def test_incident_rate(self) -> None:
        entities = [
            map_card_to_entity(self.card_aqui, row={"risk_score": 60}),
            map_card_to_entity(self.card_done, row={"risk_score": 5}),
        ]
        metrics = compute_business_metrics(entities)
        self.assertIn("incident_rate", metrics)
        self.assertGreater(metrics["incident_rate"]["value"], 0)

    def test_risk_exposure_index(self) -> None:
        entities = [map_card_to_entity(self.card_aqui, row={"risk_score": 80})]
        metrics = compute_business_metrics(entities)
        self.assertGreater(metrics["risk_exposure_index"]["value"], 0)

    def test_domain_insights(self) -> None:
        entities = [
            map_card_to_entity(self.card_aqui, row={"risk_score": 70}),
            map_card_to_entity(self.card_done, row={"risk_score": 10}),
        ]
        insights = generate_domain_insights(entities)
        self.assertTrue(len(insights) > 0)

    def test_domain_insights_blocked_member(self) -> None:
        self.card_aqui.status = "Bloqueado"
        entities = [map_card_to_entity(self.card_aqui, row={"risk_score": 60, "assignees": ["Carlos"]})]
        insights = generate_domain_insights(entities)
        self.assertTrue(any("blocked" in i.lower() or "Carlos" in i for i in insights))

    def test_empty_metrics(self) -> None:
        from apps.intelligence.services.semantic_layer.metrics import compute_business_metrics

        metrics = compute_business_metrics([])
        self.assertEqual(metrics["incident_rate"]["value"], 0.0)
