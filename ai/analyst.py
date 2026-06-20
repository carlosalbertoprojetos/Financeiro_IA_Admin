import json
import logging
from typing import Any

from django.conf import settings

from ai.exceptions import AIAnalysisError, AIConfigurationError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Você é um analista de inteligência operacional especializado em fluxo de trabalho Kanban/Trello.

Receberá métricas agregadas de um board (lead time, cycle time, throughput, aging, delay rate, rework rate, gaps).

Gere um diagnóstico operacional em português do Brasil, objetivo e acionável.

Responda SOMENTE com JSON válido neste formato:
{
  "executive_summary": "string com 2-4 frases",
  "problems": [
    {
      "title": "string",
      "description": "string",
      "severity": "high|medium|low",
      "evidence": "string opcional com base nas métricas"
    }
  ],
  "risks": [
    {
      "title": "string",
      "description": "string",
      "impact": "high|medium|low",
      "likelihood": "high|medium|low"
    }
  ],
  "recommendations": [
    {
      "title": "string",
      "action": "string",
      "priority": "high|medium|low",
      "expected_outcome": "string"
    }
  ]
}

Regras:
- Baseie-se apenas nas métricas fornecidas; não invente números.
- Se faltar dado, declare a limitação em problems ou risks.
- Priorize clareza executiva sobre detalhe técnico.
- problems, risks e recommendations devem ser listas (podem ser vazias).
""".strip()

REQUIRED_TOP_LEVEL_KEYS = ("executive_summary", "problems", "risks", "recommendations")
REQUIRED_LIST_KEYS = ("problems", "risks", "recommendations")


def analyze_metrics(
    metrics: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """
    Generate a structured operational diagnosis from aggregated metrics.

    Args:
        metrics: Aggregated metrics payload (overview, gaps, team, etc.).
        api_key: Optional OpenAI API key override.
        model: Optional OpenAI model override.
        client: Optional injected OpenAI client (for tests).
    """
    resolved_key = api_key or settings.OPENAI_API_KEY
    resolved_model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    if client is None and not resolved_key:
        raise AIConfigurationError("OPENAI_API_KEY must be configured")

    compact = compact_metrics(metrics)
    raw = _call_openai(
        compact,
        api_key=resolved_key,
        model=resolved_model,
        client=client,
    )
    diagnosis = _validate_diagnosis(raw)

    return {
        "board_id": metrics.get("board_id") or compact.get("board_id"),
        "generated_at": metrics.get("generated_at") or compact.get("generated_at"),
        "model": resolved_model,
        **diagnosis,
    }


def compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Reduce aggregated metrics to summaries suitable for LLM input."""
    if "overview" in metrics or "gaps" in metrics or "team" in metrics:
        return {
            "board_id": metrics.get("board_id"),
            "generated_at": metrics.get("generated_at"),
            "overview": _compact_section(metrics.get("overview")),
            "gaps": _compact_section(metrics.get("gaps")),
            "team": _compact_team(metrics.get("team")),
        }

    return _compact_section(metrics) or {}


def _compact_section(section: dict[str, Any] | None) -> dict[str, Any] | None:
    if not section:
        return None

    compact: dict[str, Any] = {
        "board_id": section.get("board_id"),
        "generated_at": section.get("generated_at"),
    }

    if "counts" in section:
        compact["counts"] = section["counts"]

    if "summary" in section:
        compact["summary"] = section["summary"]

    if "thresholds" in section:
        compact["thresholds"] = section["thresholds"]

    if "kpis" in section:
        compact["kpis"] = {
            name: _compact_kpi(kpi)
            for name, kpi in section["kpis"].items()
        }

    if "gaps" in section and isinstance(section["gaps"], dict):
        compact["gaps"] = {
            gap_type: _compact_gap_items(items)
            for gap_type, items in section["gaps"].items()
        }

    return compact


def _compact_kpi(kpi: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "metric": kpi.get("metric"),
        "unit": kpi.get("unit"),
        "summary": kpi.get("summary"),
    }
    if "series" in kpi:
        compact["series"] = kpi["series"][:8]
    return compact


def _compact_gap_items(items: list[dict[str, Any]], limit: int = 10) -> dict[str, Any]:
    return {
        "count": len(items),
        "sample": items[:limit],
    }


def _compact_team(team: dict[str, Any] | None) -> dict[str, Any] | None:
    if not team:
        return None

    members = []
    for member in team.get("members", [])[:12]:
        members.append(
            {
                "member_id": member.get("member_id"),
                "member_name": member.get("member_name"),
                "card_count": member.get("card_count"),
                "metrics": {
                    name: _compact_kpi(kpi)
                    for name, kpi in member.get("metrics", {}).items()
                },
            }
        )

    unassigned = team.get("unassigned") or {}
    return {
        "members": members,
        "unassigned": {
            "card_count": unassigned.get("card_count", 0),
            "metrics": {
                name: _compact_kpi(kpi)
                for name, kpi in unassigned.get("metrics", {}).items()
            },
        },
    }


def _call_openai(
    metrics_payload: dict[str, Any],
    *,
    api_key: str,
    model: str,
    client: Any | None,
) -> dict[str, Any]:
    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

    user_content = json.dumps(metrics_payload, ensure_ascii=False, default=str)

    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
    except Exception as exc:
        raise AIAnalysisError(f"OpenAI request failed: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise AIAnalysisError("OpenAI returned an empty response")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIAnalysisError("OpenAI returned invalid JSON") from exc


def _validate_diagnosis(payload: dict[str, Any]) -> dict[str, Any]:
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            raise AIAnalysisError(f"OpenAI response missing required key: {key}")

    for key in REQUIRED_LIST_KEYS:
        if not isinstance(payload[key], list):
            raise AIAnalysisError(f"OpenAI response key '{key}' must be a list")

    if not isinstance(payload["executive_summary"], str):
        raise AIAnalysisError("OpenAI response executive_summary must be a string")

    return {
        "executive_summary": payload["executive_summary"].strip(),
        "problems": payload["problems"],
        "risks": payload["risks"],
        "recommendations": payload["recommendations"],
    }
