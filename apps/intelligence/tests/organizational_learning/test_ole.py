"""OLE — Organizational Learning Engine tests."""

from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from apps.intelligence.models import DecisionEffectivenessRecord, OrganizationalMemory
from apps.intelligence.services.organizational_learning.knowledge_graph.graph import build_knowledge_graph
from apps.intelligence.services.organizational_learning.maturity.index import compute_eor_maturity_index
from apps.intelligence.services.organizational_learning.memory.storage import record_lesson_from_effectiveness
from apps.intelligence.services.organizational_learning.outcomes.evaluator import (
    OUTCOME_FAILURE,
    OUTCOME_LOW_IMPACT,
    OUTCOME_SUCCESS,
    evaluate_action_outcome,
)
from apps.intelligence.services.organizational_learning.patterns.analyzer import (
    analyze_action_patterns,
    get_action_historical_stats,
)
from apps.intelligence.services.organizational_learning.pipeline import record_action_learning
from apps.intelligence.services.organizational_learning.playbooks.engine import generate_playbooks
from apps.intelligence.services.organizational_learning.scoring.effectiveness_scorer import compute_effectiveness_score
from apps.intelligence.services.decision_layer.action_generator import generate_actions_from_entity


def _seed_effectiveness(
    *,
    action_type: str = "ESCALATE_TASK",
    risk_before: float = 85,
    risk_after: float = 40,
    outcome: str = OUTCOME_SUCCESS,
    eff: float = 88,
    category: str = "FINANCEIRO",
    board_id: str = "board1",
    decision_id: str = "",
) -> DecisionEffectivenessRecord:
    did = decision_id or f"dec_{action_type}_{DecisionEffectivenessRecord.objects.count()}"
    return DecisionEffectivenessRecord.objects.create(
        decision_id=did,
        action_type=action_type,
        risk_before=risk_before,
        risk_after=risk_after,
        sla_before=risk_before,
        sla_after=risk_after,
        execution_time=3600,
        outcome_score=eff,
        effectiveness_score=eff,
        outcome_label=outcome,
        board_id=board_id,
        category=category,
        owner="manager1",
    )


class OutcomeEngineTests(TestCase):
    def test_escalate_success(self) -> None:
        outcome = evaluate_action_outcome(
            action_type="ESCALATE_TASK",
            before={"risk_score": 85, "sla_breach_probability": 85},
            after={"risk_score": 40, "sla_breach_probability": 40},
            impact={"problem_resolved": True},
        )
        self.assertEqual(outcome["outcome_label"], OUTCOME_SUCCESS)
        self.assertGreater(outcome["risk_reduction_pct"], 40)

    def test_reassign_low_impact(self) -> None:
        outcome = evaluate_action_outcome(
            action_type="REASSIGN_OWNER",
            before={"risk_score": 70, "sla_breach_probability": 70},
            after={"risk_score": 68, "sla_breach_probability": 68},
        )
        self.assertEqual(outcome["outcome_label"], OUTCOME_LOW_IMPACT)

    def test_failure_when_risk_increases(self) -> None:
        outcome = evaluate_action_outcome(
            action_type="ADJUST_PRIORITY",
            before={"risk_score": 50},
            after={"risk_score": 60},
        )
        self.assertEqual(outcome["outcome_label"], OUTCOME_FAILURE)


class ScoringTests(TestCase):
    def test_success_high_score(self) -> None:
        outcome = evaluate_action_outcome(
            action_type="ESCALATE_TASK",
            before={"risk_score": 85},
            after={"risk_score": 40},
            impact={"problem_resolved": True},
        )
        outcome_score, eff = compute_effectiveness_score(outcome, execution_time_ms=1800)
        self.assertGreater(outcome_score, 50)
        self.assertGreater(eff, 40)

    def test_failure_low_score(self) -> None:
        outcome = {"outcome_label": OUTCOME_FAILURE, "risk_delta": 10, "risk_reduction_pct": -20}
        outcome_score, eff = compute_effectiveness_score(outcome)
        self.assertLess(outcome_score, 30)


class PatternAnalyzerTests(TestCase):
    def setUp(self) -> None:
        for _ in range(5):
            _seed_effectiveness(action_type="ESCALATE_TASK", eff=90)
        for _ in range(3):
            _seed_effectiveness(action_type="REASSIGN_OWNER", risk_after=68, eff=35, outcome=OUTCOME_LOW_IMPACT)

    def test_most_effective_actions(self) -> None:
        patterns = analyze_action_patterns(board_id="board1")
        self.assertGreaterEqual(patterns["total_records"], 8)
        self.assertEqual(patterns["most_effective_actions"][0]["action_type"], "ESCALATE_TASK")

    def test_historical_stats(self) -> None:
        stats = get_action_historical_stats("ESCALATE_TASK", category="FINANCEIRO", board_id="board1")
        self.assertEqual(stats["sample_size"], 5)
        self.assertEqual(stats["success_rate_pct"], 100.0)
        self.assertGreater(stats["avg_risk_reduction_pct"], 40)


class PlaybookEngineTests(TestCase):
    def setUp(self) -> None:
        for i in range(4):
            _seed_effectiveness(decision_id=f"dec_pb_{i}")

    def test_generate_playbooks_from_evidence(self) -> None:
        playbooks = generate_playbooks(board_id="board1", min_sample_size=3)
        self.assertGreaterEqual(len(playbooks), 1)
        self.assertTrue(playbooks[0]["evidence_based"])
        self.assertGreaterEqual(playbooks[0]["sample_size"], 3)


class KnowledgeGraphTests(TestCase):
    def test_graph_structure(self) -> None:
        _seed_effectiveness()
        graph = build_knowledge_graph(board_id="board1")
        self.assertGreater(len(graph["nodes"]), 0)
        self.assertGreater(len(graph["edges"]), 0)
        types = {n["type"] for n in graph["nodes"]}
        self.assertIn("action", types)
        self.assertIn("problem", types)


class OrganizationalMemoryTests(TestCase):
    def test_lesson_from_success(self) -> None:
        record = {
            "decision_id": "dec1",
            "action_type": "ESCALATE_TASK",
            "outcome_label": OUTCOME_SUCCESS,
            "effectiveness_score": 85,
            "risk_before": 80,
            "risk_after": 35,
            "category": "FINANCEIRO",
            "board_id": "b1",
        }
        record_lesson_from_effectiveness(record)
        self.assertTrue(OrganizationalMemory.objects.filter(memory_type="lesson_learned").exists())
        self.assertTrue(OrganizationalMemory.objects.filter(memory_type="playbook_candidate").exists())


class MaturityIndexTests(TestCase):
    def test_maturity_with_data(self) -> None:
        _seed_effectiveness()
        result = compute_eor_maturity_index(board_id="board1")
        self.assertIn("eor_maturity_index", result)
        self.assertGreater(result["eor_maturity_index"], 0)
        self.assertIn("components", result)

    def test_maturity_empty(self) -> None:
        result = compute_eor_maturity_index()
        self.assertIn("eor_maturity_index", result)


class RecommendationEvolutionTests(TestCase):
    def test_actions_include_historical_stats(self) -> None:
        for _ in range(3):
            _seed_effectiveness(action_type="ESCALATE_TASK", category="FINANCEIRO")
        entity = {
            "card_id": "c1",
            "title": "Finance task",
            "risk_score": 80,
            "category": "FINANCEIRO",
            "entity_type": "INCIDENT",
            "status": "DELAYED",
        }
        actions = generate_actions_from_entity(entity, board_id="board1")
        escalate = next(a for a in actions if a.action_type == "ESCALATE_TASK")
        self.assertIn("historical_success_rate_pct", escalate.params)
        self.assertEqual(escalate.params["historical_success_rate_pct"], 100.0)


class RecordLearningPipelineTests(TestCase):
    def test_record_action_learning(self) -> None:
        result = record_action_learning(
            decision_id="dec_test",
            action_type="ESCALATE_TASK",
            before={"risk_score": 85, "sla_breach_probability": 85},
            after={"risk_score": 40, "sla_breach_probability": 40},
            impact={"problem_resolved": True},
            board_id="board1",
            category="FINANCEIRO",
        )
        assert result is not None
        self.assertEqual(DecisionEffectivenessRecord.objects.count(), 1)
        self.assertEqual(result.outcome_label, OUTCOME_SUCCESS)


class LearningApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        _seed_effectiveness()

    def test_dashboard(self) -> None:
        r = self.client.get("/api/learning/dashboard/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("eor_maturity_index", r.data)

    def test_patterns(self) -> None:
        r = self.client.get("/api/learning/patterns/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("most_effective_actions", r.data)

    def test_action_stats(self) -> None:
        r = self.client.get("/api/learning/actions/ESCALATE_TASK/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["action_type"], "ESCALATE_TASK")

    def test_knowledge_graph(self) -> None:
        r = self.client.get("/api/learning/knowledge-graph/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("nodes", r.data)

    def test_maturity(self) -> None:
        r = self.client.get("/api/learning/maturity/?board_id=board1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("eor_maturity_index", r.data)
