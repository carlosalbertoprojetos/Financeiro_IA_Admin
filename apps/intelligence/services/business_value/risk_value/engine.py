from __future__ import annotations

from typing import Any

from apps.intelligence.services.business_value.config import base_impact_brl


def risk_score_to_probability(risk_score: float) -> float:
    """Map risk score 0-100 to probability 0-1 — linear from observed risk engine score."""
    return min(1.0, max(0.0, risk_score / 100))


def compute_expected_loss(
    *,
    risk_score: float,
    impact_brl: float | None = None,
) -> dict[str, Any]:
    """
    Convert risk_score to expected financial loss.
    expected_loss = probability(risk_score) * impact_brl
    """
    impact = impact_brl if impact_brl is not None else base_impact_brl() * (risk_score / 100)
    probability = risk_score_to_probability(risk_score)
    expected = probability * impact
    confidence = 0.8 if risk_score > 0 else 0.3

    return {
        "risk_score": risk_score,
        "probability": round(probability, 4),
        "probability_pct": round(probability * 100, 1),
        "impact_brl": round(impact, 2),
        "expected_loss": round(expected, 2),
        "confidence_score": confidence,
        "formula": "expected_loss = (risk_score/100) * impact_brl",
    }


def compute_avoided_loss(
    *,
    risk_before: float,
    risk_after: float,
    impact_brl: float | None = None,
) -> dict[str, Any]:
    """Avoided loss = expected_loss(before) - expected_loss(after)."""
    before = compute_expected_loss(risk_score=risk_before, impact_brl=impact_brl)
    after = compute_expected_loss(risk_score=risk_after, impact_brl=impact_brl)
    avoided = max(0, before["expected_loss"] - after["expected_loss"])
    confidence = min(before["confidence_score"], after["confidence_score"])

    return {
        "avoided_loss": round(avoided, 2),
        "expected_loss_before": before["expected_loss"],
        "expected_loss_after": after["expected_loss"],
        "confidence_score": confidence,
        "before": before,
        "after": after,
    }
