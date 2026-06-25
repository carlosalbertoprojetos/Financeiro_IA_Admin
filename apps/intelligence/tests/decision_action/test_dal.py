"""DAL — Decision Action Layer tests."""

from __future__ import annotations

import os
from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.intelligence.models import ActionExecutionLog, DecisionRecord
from apps.intelligence.services.decision_layer.action_generator import (
    generate_actions_from_entity,
    generate_actions_from_insight,
    generate_decisions_from_output,
)
from apps.intelligence.services.decision_layer.approval.flow import approve_action, request_approval
from apps.intelligence.services.decision_layer.feedback.loop import measure_action_impact, record_feedback
from apps.intelligence.services.decision_layer.guards.rules import validate_action
from apps.intelligence.services.decision_layer.models import DecisionObject, DecisionPriority
from apps.intelligence.services.decision_layer.orchestrator import ActionOrchestrator, execute_decision_action
from apps.intelligence.services.decision_layer.prioritizer import build_action_queue, prioritize_decisions
from apps.intelligence.services.decision_layer.queue.manager import (
    enqueue_decision,
    get_pending_queue,
    load_decision,
    mark_executed,
    mark_failed,
    mark_in_progress,
)
from apps.intelligence.services.decision_layer.trello_executor import TrelloActionExecutor
from integrations.trello.models import Board, BoardList, Card
from apps.intelligence.services.query_engine.runner import execute_eql_query
from apps.intelligence.tests.test_report_query import ReportQueryTestMixin


class ActionGenerationTests(TestCase):
    def test_high_risk_entity_generates_escalation(self) -> None:
        entity = {
            "card_id": "card_1",
            "title": "Critical task",
            "risk_score": 80,
            "risk_flags": ["overdue"],
            "entity_type": "INCIDENT",
            "status": "DELAYED",
        }
        actions = generate_actions_from_entity(entity, board_id="board1")
        types = {a.action_type for a in actions}
        self.assertIn("ESCALATE_TASK", types)
        self.assertIn("CREATE_ALERT", types)

    def test_insight_generates_intervention(self) -> None:
        actions = generate_actions_from_insight("Blocked members causing bottlenecks", board_id="b1")
        self.assertTrue(len(actions) >= 1)
        self.assertIn(actions[0].action_type, ("ESCALATE_TASK", "MANAGERIAL_INTERVENTION", "CREATE_ALERT"))

    def test_output_generates_decisions(self) -> None:
        output = {
            "summary": {"board_id": "b1"},
            "entities": [{
                "card_id": "c1",
                "title": "Task A",
                "risk_score": 55,
                "entity_type": "TASK",
                "status": "DELAYED",
            }],
            "domain_insights": ["Incidents increase after assignee changes"],
        }
        decisions = generate_decisions_from_output(output, source_trace_id="trace-1")
        self.assertGreaterEqual(len(decisions), 2)
        self.assertTrue(all(d.source_trace_id == "trace-1" for d in decisions))


class PrioritizationTests(TestCase):
    def test_critical_decisions_rank_first(self) -> None:
        low = DecisionObject.create(insight="low", priority=DecisionPriority.LOW.value, score=10)
        critical = DecisionObject.create(insight="critical", priority=DecisionPriority.CRITICAL.value, score=90)
        ordered = prioritize_decisions([low, critical])
        self.assertEqual(ordered[0].priority, DecisionPriority.CRITICAL.value)

    def test_action_queue_ordering(self) -> None:
        d1 = DecisionObject.create(insight="a", priority="HIGH", score=80)
        d1.recommended_actions = [{"action_type": "CREATE_ALERT", "execution_mode": "AUTOMATIC"}]
        d2 = DecisionObject.create(insight="b", priority="LOW", score=20)
        d2.recommended_actions = [{"action_type": "MANAGERIAL_INTERVENTION", "execution_mode": "MANUAL"}]
        queue = build_action_queue(prioritize_decisions([d2, d1]))
        self.assertEqual(queue[0]["decision_id"], d1.id)


class GuardTests(TestCase):
    def test_destructive_action_requires_approval(self) -> None:
        guard = validate_action({"action_type": "REOPEN_CARD", "execution_mode": "AUTOMATIC"})
        self.assertTrue(guard["requires_approval"])
        self.assertFalse(guard["allowed"])

    def test_bulk_action_blocked(self) -> None:
        guard = validate_action({"action_type": "ADJUST_PRIORITY", "execution_mode": "SEMI_AUTOMATIC"}, bulk_card_count=10)
        self.assertFalse(guard["allowed"])
        self.assertEqual(guard["blocked_by"], "bulk_limit")

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "false"})
    def test_auto_disabled_by_default(self) -> None:
        guard = validate_action({"action_type": "CREATE_ALERT", "execution_mode": "AUTOMATIC"})
        self.assertFalse(guard["allowed"])

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "true", "DAL_MAX_AUTO_ACTIONS_PER_HOUR": "2"})
    def test_rate_limit_blocks_auto(self) -> None:
        guard = validate_action(
            {"action_type": "CREATE_ALERT", "execution_mode": "AUTOMATIC"},
            auto_count_last_hour=2,
        )
        self.assertFalse(guard["allowed"])
        self.assertEqual(guard["blocked_by"], "rate_limit")

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "true"})
    def test_loop_guard_blocks_repeat_action(self) -> None:
        recent = [{"action_type": "ADD_COMMENT", "target_card_id": "c1", "within_cooldown": True}]
        guard = validate_action(
            {"action_type": "ADD_COMMENT", "execution_mode": "AUTOMATIC", "target_card_id": "c1"},
            recent_executions=recent,
        )
        self.assertFalse(guard["allowed"])
        self.assertEqual(guard["blocked_by"], "loop_guard")


class ApprovalFlowTests(TestCase):
    def test_semi_automatic_requires_approval(self) -> None:
        decision = DecisionObject.create(
            insight="test",
            recommended_actions=[{
                "action_type": "ESCALATE_TASK",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "c1",
            }],
        ).to_dict()
        action = decision["recommended_actions"][0]
        approval = request_approval(decision, action)
        self.assertEqual(approval["status"], "PENDING_APPROVAL")

    def test_approve_action(self) -> None:
        decision = DecisionObject.create(
            insight="test",
            recommended_actions=[{"action_type": "CREATE_ALERT", "execution_mode": "SEMI_AUTOMATIC"}],
        ).to_dict()
        result = approve_action(decision, approved_by="manager1")
        self.assertTrue(result["approved"])


class FeedbackLoopTests(TestCase):
    def test_risk_reduction_detected(self) -> None:
        impact = measure_action_impact(
            before={"risk_score": 80, "status": "OPEN"},
            after={"risk_score": 50, "status": "OPEN"},
            action_type="ESCALATE_TASK",
        )
        self.assertTrue(impact["risk_reduced"])
        self.assertLess(impact["risk_delta"], 0)

    def test_feedback_record(self) -> None:
        impact = measure_action_impact(
            before={"risk_score": 70},
            after={"risk_score": 40},
            action_type="ADJUST_PRIORITY",
        )
        fb = record_feedback("dec-1", impact, trace_id="trace-1")
        self.assertTrue(fb["feeds_risk_model"])


class TrelloExecutorTests(TestCase):
    def test_dry_run_does_not_call_api(self) -> None:
        executor = TrelloActionExecutor(dry_run=True)
        result = executor.execute({
            "action_type": "ADD_COMMENT",
            "target_card_id": "card123",
            "params": {"text": "test"},
        })
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["provider"], "trello")

    def _mock_client(self) -> mock.Mock:
        client = mock.Mock()
        client.add_comment.return_value = {"id": "comment1"}
        client.update_card.return_value = {"id": "card123"}
        client.add_member_to_card.return_value = {"id": "member1"}
        return client

    def test_add_comment_calls_api(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        result = executor.execute({
            "action_type": "ADD_COMMENT",
            "target_card_id": "card123",
            "params": {"text": "hello"},
        })
        executor._client.add_comment.assert_called_once_with("card123", "hello")
        self.assertEqual(result["action"], "add_comment")

    def test_reopen_card(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        result = executor.execute({"action_type": "REOPEN_CARD", "target_card_id": "c1", "params": {}})
        executor._client.update_card.assert_called_once_with("c1", closed=False)
        self.assertEqual(result["action"], "reopen")

    def test_adjust_priority(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        executor.execute({"action_type": "ADJUST_PRIORITY", "target_card_id": "c1", "params": {"pos": "top"}})
        executor._client.update_card.assert_called_with("c1", pos="top")

    def test_reassign_owner_with_member(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        result = executor.execute({
            "action_type": "REASSIGN_OWNER",
            "target_card_id": "c1",
            "params": {"member_id": "m1"},
        })
        self.assertEqual(result["action"], "reassign")

    def test_reassign_without_member_suggested(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        result = executor.execute({"action_type": "REASSIGN_OWNER", "target_card_id": "c1", "params": {}})
        self.assertEqual(result["status"], "suggested")

    def test_move_card(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        executor.execute({"action_type": "MOVE_CARD", "target_card_id": "c1", "params": {"list_id": "list1"}})
        executor._client.update_card.assert_called_with("c1", idList="list1")

    def test_move_card_missing_list_raises(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        with self.assertRaises(ValueError):
            executor.execute({"action_type": "MOVE_CARD", "target_card_id": "c1", "params": {}})

    def test_escalate_task(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        executor._client = self._mock_client()
        result = executor.execute({
            "action_type": "ESCALATE_TASK",
            "target_card_id": "c1",
            "params": {"reason": "SLA breach"},
        })
        self.assertEqual(result["action"], "escalate")
        executor._client.add_comment.assert_called_once()
        executor._client.update_card.assert_called_with("c1", pos="top")

    def test_unsupported_action_raises(self) -> None:
        executor = TrelloActionExecutor(dry_run=False)
        with self.assertRaises(ValueError):
            executor.execute({"action_type": "UNKNOWN", "target_card_id": "c1", "params": {}})


class QueueManagerTests(TestCase):
    def test_mark_in_progress_and_executed(self) -> None:
        decision = DecisionObject.create(
            insight="queue test",
            recommended_actions=[{"action_type": "CREATE_ALERT", "execution_mode": "MANUAL"}],
        )
        record = enqueue_decision(decision.to_dict())
        mark_in_progress(record.decision_id)
        loaded = load_decision(record.decision_id)
        self.assertEqual(loaded["status"], "IN_PROGRESS")
        mark_executed(record.decision_id, {"action_type": "CREATE_ALERT", "result": {"ok": True}})
        loaded = load_decision(record.decision_id)
        self.assertEqual(loaded["status"], "EXECUTED")
        self.assertEqual(len(loaded["execution_history"]), 1)

    def test_mark_failed_retries_then_dead_letters(self) -> None:
        decision = DecisionObject.create(
            insight="retry test",
            recommended_actions=[{"action_type": "CREATE_ALERT", "execution_mode": "MANUAL"}],
        )
        record = enqueue_decision(decision.to_dict())
        for _ in range(2):
            result = mark_failed(record.decision_id, "transient error")
            self.assertEqual(result["status"], "retry_scheduled")
        result = mark_failed(record.decision_id, "persistent error")
        self.assertEqual(result["status"], "dead_letter")
        loaded = load_decision(record.decision_id)
        self.assertEqual(loaded["status"], "DEAD_LETTER")
        self.assertEqual(loaded["retry_count"], 3)

    def test_mark_failed_not_found(self) -> None:
        result = mark_failed("missing-id", "err")
        self.assertEqual(result["status"], "not_found")

    def test_pending_queue_filters_by_board(self) -> None:
        d1 = DecisionObject.create(insight="a", board_id="board_a")
        d2 = DecisionObject.create(insight="b", board_id="board_b")
        enqueue_decision(d1.to_dict())
        enqueue_decision(d2.to_dict())
        queue = get_pending_queue(board_id="board_a")
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["board_id"], "board_a")


class ExecutionOrchestratorTests(TestCase):
    def setUp(self) -> None:
        self.board = Board.objects.create(trello_id="dal_board", name="DAL Board")
        self.board_list = BoardList.objects.create(
            trello_id="dal_list", board=self.board, name="Doing", position=0.0,
        )
        self.card = Card.objects.create(
            trello_id="card_dal",
            board=self.board,
            board_list=self.board_list,
            title="Test card",
            status="Em Andamento",
        )
        decision = DecisionObject.create(
            insight="Alert test",
            recommended_actions=[{
                "action_type": "CREATE_ALERT",
                "execution_mode": "MANUAL",
                "params": {"severity": "HIGH"},
                "target_card_id": "",
            }],
        )
        self.decision = enqueue_decision(decision.to_dict())

    def test_manual_action_suggested_not_executed(self) -> None:
        result = execute_decision_action(self.decision.decision_id, dry_run=True)
        self.assertEqual(result["status"], "SUGGESTED")

    def test_semi_automatic_pending_approval(self) -> None:
        decision = DecisionObject.create(
            insight="Escalate",
            recommended_actions=[{
                "action_type": "ESCALATE_TASK",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "card_x",
                "params": {},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        result = execute_decision_action(record.decision_id, dry_run=True)
        self.assertEqual(result["status"], "PENDING_APPROVAL")
        self.assertEqual(ActionExecutionLog.objects.filter(status="PENDING_APPROVAL").count(), 1)

    def test_not_found_and_invalid_index(self) -> None:
        self.assertEqual(execute_decision_action("missing")["status"], "NOT_FOUND")
        result = execute_decision_action(self.decision.decision_id, action_index=99)
        self.assertEqual(result["status"], "INVALID_ACTION_INDEX")

    def test_blocked_automatic_reopen(self) -> None:
        decision = DecisionObject.create(
            insight="Reopen",
            recommended_actions=[{
                "action_type": "REOPEN_CARD",
                "execution_mode": "AUTOMATIC",
                "target_card_id": "card_dal",
                "params": {},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        result = execute_decision_action(record.decision_id, approved_by="manager")
        self.assertEqual(result["status"], "BLOCKED")

    @mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "true"})
    def test_executed_create_alert_with_approval(self) -> None:
        decision = DecisionObject.create(
            insight="Alert exec",
            board_id="dal_board",
            context={"entity": {"entity_type": "TASK", "category": "OPS"}},
            recommended_actions=[{
                "action_type": "CREATE_ALERT",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "card_dal",
                "params": {"severity": "HIGH"},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        result = execute_decision_action(record.decision_id, approved_by="manager1")
        self.assertEqual(result["status"], "EXECUTED")
        self.assertIn("impact", result)
        self.assertIn("learning", result)
        self.assertIn("value", result)
        loaded = load_decision(record.decision_id)
        self.assertEqual(loaded["status"], "EXECUTED")

    def test_execution_failure_marks_retry(self) -> None:
        decision = DecisionObject.create(
            insight="Fail",
            recommended_actions=[{
                "action_type": "WEBHOOK_NOTIFY",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "",
                "params": {},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        orchestrator = ActionOrchestrator(dry_run=False)
        with mock.patch.object(orchestrator, "_dispatch", side_effect=RuntimeError("dispatch failed")):
            result = orchestrator.execute_action(
                record.to_dict() if hasattr(record, "to_dict") else load_decision(record.decision_id),
                load_decision(record.decision_id)["recommended_actions"][0],
                approved_by="manager",
            )
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("retry", result)

    def test_orchestrator_dispatch_channels(self) -> None:
        orch = ActionOrchestrator(dry_run=True)
        webhook = orch._dispatch({"action_type": "WEBHOOK_NOTIFY", "params": {"url": "http://x"}})
        self.assertFalse(webhook["dispatched"])
        intervention = orch._dispatch({"action_type": "MANAGERIAL_INTERVENTION", "params": {}})
        self.assertFalse(intervention["executed"])
        with self.assertRaises(ValueError):
            orch._dispatch({"action_type": "NO_SUCH_ACTION"})


class ActionApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_overview(self) -> None:
        r = self.client.get("/api/actions/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("endpoints", r.data)

    def test_generate_decisions(self) -> None:
        r = self.client.post("/api/actions/generate/", {
            "output": {
                "summary": {"board_id": "b1"},
                "entities": [{"card_id": "c1", "title": "T", "risk_score": 60, "entity_type": "TASK"}],
            },
            "trace_id": "trace-abc",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("decisions", r.data)

    def test_queue_empty(self) -> None:
        r = self.client.get("/api/actions/queue/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("queue", r.data)

    def test_execute_missing_decision_id(self) -> None:
        r = self.client.post("/api/actions/execute/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_generate_missing_output(self) -> None:
        r = self.client.post("/api/actions/generate/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_decision_detail_not_found(self) -> None:
        r = self.client.get("/api/actions/decisions/does-not-exist/")
        self.assertEqual(r.status_code, 404)

    def test_approve_and_reject_flow(self) -> None:
        reject_decision = DecisionObject.create(
            insight="API reject",
            recommended_actions=[{
                "action_type": "CREATE_ALERT",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "",
                "params": {},
            }],
        )
        record = enqueue_decision(reject_decision.to_dict())
        reject = self.client.post("/api/actions/reject/", {
            "decision_id": record.decision_id,
            "rejected_by": "ops",
            "reason": "not needed",
        }, format="json")
        self.assertEqual(reject.status_code, 200)
        self.assertFalse(reject.data["approved"])

        approve_decision = DecisionObject.create(
            insight="API approve",
            recommended_actions=[{
                "action_type": "CREATE_ALERT",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "",
                "params": {},
            }],
        )
        record2 = enqueue_decision(approve_decision.to_dict())
        with mock.patch.dict(os.environ, {"DAL_AUTO_EXECUTION": "true"}):
            approve = self.client.post("/api/actions/approve/", {
                "decision_id": record2.decision_id,
                "approved_by": "manager",
                "dry_run": True,
            }, format="json")
        self.assertEqual(approve.status_code, 200)
        self.assertTrue(approve.data["approval"]["approved"])

    def test_execute_returns_202_for_pending_approval(self) -> None:
        decision = DecisionObject.create(
            insight="Pending",
            recommended_actions=[{
                "action_type": "ESCALATE_TASK",
                "execution_mode": "SEMI_AUTOMATIC",
                "target_card_id": "card_x",
                "params": {},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        r = self.client.post("/api/actions/execute/", {"decision_id": record.decision_id}, format="json")
        self.assertEqual(r.status_code, 202)
        self.assertEqual(r.data["status"], "PENDING_APPROVAL")

    def test_execute_returns_403_when_blocked(self) -> None:
        decision = DecisionObject.create(
            insight="Blocked",
            recommended_actions=[{
                "action_type": "REOPEN_CARD",
                "execution_mode": "AUTOMATIC",
                "target_card_id": "card_x",
                "params": {},
            }],
        )
        record = enqueue_decision(decision.to_dict())
        r = self.client.post("/api/actions/execute/", {
            "decision_id": record.decision_id,
            "approved_by": "manager",
        }, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.data["status"], "BLOCKED")


class RunnerIntegrationTests(ReportQueryTestMixin, TestCase):
    def test_query_output_includes_decisions(self) -> None:
        query = """
REPORT:
TYPE = EXECUTIVE
FILTER:
PERIOD = LAST_30_DAYS
LIMIT:
100
"""
        result = execute_eql_query(query, board_id="rq_board", use_cache=False)
        self.assertIn("decisions", result)
        self.assertIn("action_queue", result)
        self.assertIn("decision_summary", result)
