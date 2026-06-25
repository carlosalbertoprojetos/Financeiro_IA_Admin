from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from django.core.cache import cache

from apps.intelligence.models import ReportQueryExecutionTrace, ReportQueryLog
from apps.intelligence.services.core_model.enforcer import enforce_eql_ast, enforce_query_plan, govern_pipeline
from apps.intelligence.services.core_model.errors import GovernanceError
from apps.intelligence.services.eql.errors import (
    EQLError,
    MissingLimitError,
    QueryCostRejectedError,
    QueryGuardRejectedError,
    QueryTimeoutError,
)
from apps.intelligence.services.eql.parser import parse_eql
from apps.intelligence.services.eql.validator import validate_eql
from apps.intelligence.services.observability.context import set_collector
from apps.intelligence.services.observability.error_trace import record_error_trace, record_guard_rejection
from apps.intelligence.services.observability.execution_trace import record_cache_event, start_step
from apps.intelligence.services.observability.pipeline import finalize_pipeline_trace
from apps.intelligence.services.observability.trace.collector import TraceCollector
from apps.intelligence.services.query_engine.compiler.compiler import compile_ast
from apps.intelligence.services.query_engine.cost_estimator.estimator import estimate_cost
from apps.intelligence.services.query_engine.executor import compute_actual_cost, execute_optimized_plan
from apps.intelligence.services.query_engine.guard.guard import guard_query
from apps.intelligence.services.query_engine.optimizer.optimizer import optimize_plan
from apps.intelligence.services.decision_layer.pipeline import enrich_with_decisions
from apps.intelligence.services.evolution.config import is_safe_mode
from apps.intelligence.services.evolution.pipeline.orchestrator import prepare_query_for_execution
from apps.intelligence.services.evolution.semantic_migration import migrate_entities
from apps.intelligence.services.evolution.versioning.core import version_snapshot
from apps.intelligence.services.semantic_layer.pipeline import apply_semantic_layer
from apps.intelligence.services.semantic_layer.query_resolver import resolve_semantic_to_technical

logger = logging.getLogger(__name__)

CACHE_PREFIX = "eor:eql:"
DEFAULT_TIMEOUT_MS = 120_000


def execute_eql_query(
    query_text: str,
    *,
    board_id: str = "",
    user_id: str = "anonymous",
    use_cache: bool = True,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    skip_guard: bool = False,
) -> dict[str, Any]:
    """
    Full EQL pipeline with ODTL decision tracing.
    """
    start = time.perf_counter()
    query_text, evolution_meta = prepare_query_for_execution(query_text)
    collector = TraceCollector(query_text=query_text, board_id=board_id, user_id=user_id)
    set_collector(collector)
    collector.record_input("eql", {
        "query": query_text[:5000],
        "board_id": board_id,
        "evolution": evolution_meta,
    })

    ast_dict: dict[str, Any] = {}
    query_plan_dict: dict[str, Any] = {}
    optimized_plan_dict: dict[str, Any] = {}
    cost_dict: dict[str, Any] = {}
    semantic_filters: dict[str, Any] = {}
    rejected_by_guard = False

    try:
        start_step("parse", "eql")
        parsed = parse_eql(query_text, board_id=board_id)
        validated = validate_eql(parsed)
        validated, semantic_filters = resolve_semantic_to_technical(validated)
        ast_dict = validated.to_dict()
        if semantic_filters:
            ast_dict["semantic_filters"] = semantic_filters
        collector.end_step("parse", "eql", ast_keys=list(ast_dict.keys()))

        start_step("governance_ast", "core_model")
        enforce_eql_ast(ast_dict)
        collector.end_step("governance_ast", "core_model")

        if use_cache:
            cached = _get_cache(ast_dict)
            if cached is not None:
                elapsed = int((time.perf_counter() - start) * 1000)
                record_cache_event(True)
                cached["summary"]["cache_hit"] = True
                cached["trace_id"] = collector.trace_id
                cached["query_id"] = collector.query_id
                finalize_pipeline_trace(collector, cached, query_raw=query_text, execution_ms=elapsed)
                _log_legacy(query_text, ast_dict, elapsed, user_id, "success", cache_hit=True)
                _log_execution_trace(query_text, ast_dict, {}, {}, {}, 0, elapsed, user_id, True, False, "success")
                return cached

        start_step("compile", "query_engine")
        query_plan = compile_ast(validated)
        query_plan_dict = query_plan.to_dict()
        enforce_query_plan(query_plan_dict)
        collector.end_step("compile", "query_engine")

        start_step("optimize", "optimizer")
        optimized = optimize_plan(query_plan)
        optimized_plan_dict = optimized.to_dict()
        collector.end_step("optimize", "optimizer", notes=optimized.optimization_notes)

        cost = estimate_cost(optimized)
        cost_dict = cost.to_dict()

        if not skip_guard:
            start_step("guard", "query_guard")
            try:
                guard_query(optimized, cost)
            except QueryGuardRejectedError as exc:
                record_guard_rejection(exc.message, exc.code)
                raise
            collector.end_step("guard", "query_guard")

        start_step("execute", "query_engine")
        exec_start = time.perf_counter()
        output = execute_optimized_plan(optimized, ast_dict=ast_dict, processing_start_ms=exec_start)
        collector.end_step("execute", "query_engine", matched=output["summary"].get("matched_cards", 0))

        processing_ms = int((time.perf_counter() - start) * 1000)
        if processing_ms > timeout_ms:
            raise QueryTimeoutError(f"Query exceeded timeout of {timeout_ms}ms")

        actual_cost = compute_actual_cost(
            output["summary"].get("matched_cards", 0),
            processing_ms,
            optimized,
        )

        output["query_ast"] = ast_dict
        output["query_plan"] = query_plan_dict
        output["optimized_plan"] = optimized_plan_dict
        output["cost_estimate"] = cost_dict
        output["actual_cost"] = actual_cost

        start_step("semantic_layer", "semantic")
        output = apply_semantic_layer(output, semantic_filters=semantic_filters)
        if output.get("entities"):
            from_version = evolution_meta.get("detected_version", "1.0.0")
            migrated, entity_changes = migrate_entities(output["entities"], from_version=from_version)
            output["entities"] = migrated
            if entity_changes:
                evolution_meta.setdefault("entity_migrations", []).extend(entity_changes)
        collector.end_step("semantic_layer", "semantic", entities=len(output.get("entities", [])))

        start_step("decision_layer", "dal")
        output = enrich_with_decisions(
            output,
            source_trace_id=collector.trace_id,
            owner=user_id,
            persist=False,
        )
        collector.end_step("decision_layer", "dal", decisions=len(output.get("decisions", [])))

        start_step("governance_output", "core_model")
        governance = govern_pipeline(ast=ast_dict, query_plan=query_plan_dict, output=output, strict=False)
        output["governance"] = governance
        collector.end_step("governance_output", "core_model")

        record_cache_event(False)
        if use_cache:
            _set_cache(ast_dict, output)

        output["evolution"] = {
            **evolution_meta,
            "versions": version_snapshot(),
            "safe_mode": is_safe_mode(),
        }
        output = finalize_pipeline_trace(collector, output, query_raw=query_text, execution_ms=processing_ms)

        _log_legacy(query_text, ast_dict, processing_ms, user_id, "success")
        _log_execution_trace(
            query_text, ast_dict, query_plan_dict, optimized_plan_dict, cost_dict,
            actual_cost, processing_ms, user_id, False, False, "success",
        )
        return output

    except (EQLError, GovernanceError) as exc:
        rejected_by_guard = isinstance(exc, (QueryGuardRejectedError, QueryCostRejectedError, MissingLimitError))
        elapsed = int((time.perf_counter() - start) * 1000)
        error_msg = getattr(exc, "message", str(exc))
        record_error_trace(code=getattr(exc, "code", "ERROR"), message=error_msg, layer="pipeline", query_id=collector.query_id)
        partial = {"summary": {"board_id": board_id}, "query_ast": ast_dict, "query_plan": query_plan_dict}
        finalize_pipeline_trace(collector, partial, query_raw=query_text, execution_ms=elapsed, status="error")
        _log_legacy(query_text, ast_dict, elapsed, user_id, "error", error=error_msg)
        _log_execution_trace(
            query_text, ast_dict, query_plan_dict, optimized_plan_dict, cost_dict,
            0, elapsed, user_id, False, rejected_by_guard, "error", error_msg,
        )
        set_collector(None)
        raise
    except Exception as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        record_error_trace(code="EXECUTION_ERROR", message=str(exc), layer="pipeline", query_id=collector.query_id)
        partial = {"summary": {"board_id": board_id}, "query_ast": ast_dict}
        finalize_pipeline_trace(collector, partial, query_raw=query_text, execution_ms=elapsed, status="error")
        _log_legacy(query_text, ast_dict, elapsed, user_id, "error", error=str(exc))
        _log_execution_trace(
            query_text, ast_dict, query_plan_dict, optimized_plan_dict, cost_dict,
            0, elapsed, user_id, False, False, "error", str(exc),
        )
        set_collector(None)
        raise


def _cache_key(ast_dict: dict[str, Any]) -> str:
    raw = json.dumps(ast_dict, sort_keys=True, default=str)
    return CACHE_PREFIX + hashlib.sha256(raw.encode()).hexdigest()[:32]


def _get_cache(ast_dict: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return cache.get(_cache_key(ast_dict))
    except Exception:
        return None


def _set_cache(ast_dict: dict[str, Any], result: dict[str, Any], ttl: int = 3600) -> None:
    try:
        cache.set(_cache_key(ast_dict), result, ttl)
    except Exception:
        pass


def _log_legacy(
    query_raw: str,
    query_ast: dict[str, Any],
    execution_ms: int,
    user_id: str,
    status: str,
    *,
    cache_hit: bool = False,
    error: str = "",
) -> None:
    try:
        ReportQueryLog.objects.create(
            query_raw=query_raw[:10000],
            query_ast=query_ast,
            execution_time_ms=execution_ms,
            user_id=user_id,
            status=status,
            board_id=query_ast.get("board_id", ""),
            cache_hit=cache_hit,
            error_message=error[:2000],
        )
    except Exception:
        logger.exception("Failed to log EQL query")


def _log_execution_trace(
    query_raw: str,
    ast_dict: dict[str, Any],
    query_plan: dict[str, Any],
    optimized_plan: dict[str, Any],
    cost: dict[str, Any],
    actual_cost: int,
    execution_ms: int,
    user_id: str,
    cache_hit: bool,
    rejected_by_guard: bool,
    status: str,
    error: str = "",
) -> None:
    try:
        ReportQueryExecutionTrace.objects.create(
            query_raw=query_raw[:10000],
            ast=ast_dict,
            query_plan=query_plan,
            optimized_plan=optimized_plan,
            estimated_cost=cost.get("estimated_cost", 0),
            actual_cost=actual_cost,
            execution_time_ms=execution_ms,
            user_id=user_id,
            board_id=ast_dict.get("board_id", ""),
            cache_hit=cache_hit,
            rejected_by_guard=rejected_by_guard,
            status=status,
            error_message=error[:2000],
        )
    except Exception:
        logger.exception("Failed to log query execution trace")
