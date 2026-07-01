from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


MIN_CORRELATION_SAMPLE = 4


def build_discovery_insights(
    analytical: dict[str, Any],
    executive_narrative: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = analytical.get("metrics_pack", {})
    cards = analytical.get("activity_classification", {}).get("cards", [])
    anomalies = _detect_anomalies(metrics, cards)
    patterns = _discover_patterns(metrics, cards)
    correlations = _discover_correlations(cards)
    hotspots = _build_hotspots(metrics, cards)
    opportunities = _detect_opportunities(metrics, cards, correlations)
    highlights = _build_highlights(anomalies, patterns, correlations, hotspots, opportunities)
    surprises = _build_surprises(metrics, cards, hotspots)
    forecast = _build_forecast(metrics, anomalies, patterns)
    score = _score_report_intelligence(
        anomalies=anomalies,
        patterns=patterns,
        correlations=correlations,
        hotspots=hotspots,
        opportunities=opportunities,
        highlights=highlights,
        surprises=surprises,
        forecast=forecast,
        analytical=analytical,
        executive_narrative=executive_narrative or {},
    )

    return {
        "anomalies": anomalies,
        "patterns": patterns,
        "correlations": correlations,
        "hotspots": hotspots,
        "opportunities": opportunities,
        "executive_highlights": highlights[:10],
        "executive_surprises": surprises,
        "what_happens_next": forecast,
        "report_intelligence_score": score,
        "evidence_policy": {
            "discoveries_require_evidence": True,
            "correlations_require_min_sample": MIN_CORRELATION_SAMPLE,
            "forecasts_require_observed_trend": True,
            "deterministic_generation": True,
        },
    }


def _detect_anomalies(metrics: dict[str, Any], cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    volume = metrics.get("volume", {})
    sla = metrics.get("sla", {})
    quality = metrics.get("quality", {})
    communication = metrics.get("communication", {})
    workload = metrics.get("workload", {})
    time = metrics.get("time", {})
    risks = metrics.get("risks", {})
    total = int(volume.get("total_cards") or len(cards) or 0)

    if total <= 0:
        return []

    overdue = int(sla.get("overdue_open_cards") or 0)
    if _ratio(overdue, total) >= 0.25:
        anomalies.append(
            _item(
                title="Concentracao elevada de cards vencidos",
                kind="sla",
                severity="alta",
                metric_source="metrics_pack.sla.overdue_open_cards",
                evidence=[f"{overdue} de {total} cards estao abertos e vencidos"],
                impact=4,
                confidence=0.9,
            )
        )

    without_due = int(sla.get("cards_without_due_date") or 0)
    if _ratio(without_due, total) >= 0.4:
        anomalies.append(
            _item(
                title="Muitos cards sem prazo definido",
                kind="documentacao",
                severity="media",
                metric_source="metrics_pack.sla.cards_without_due_date",
                evidence=[f"{without_due} de {total} cards nao possuem prazo"],
                impact=3,
                confidence=0.82,
            )
        )

    missing_owner = int(quality.get("missing_owner_count") or 0)
    if _ratio(missing_owner, total) >= 0.25:
        anomalies.append(
            _item(
                title="Falha de triagem: cards sem responsavel",
                kind="documentacao",
                severity="alta" if _ratio(missing_owner, total) >= 0.5 else "media",
                metric_source="metrics_pack.quality.missing_owner_count",
                evidence=[f"{missing_owner} de {total} cards estao sem responsavel"],
                impact=4,
                confidence=0.88,
            )
        )

    poor_descriptions = int(quality.get("incomplete_description_count") or 0)
    if _ratio(poor_descriptions, total) >= 0.3:
        anomalies.append(
            _item(
                title="Descricoes curtas ou insuficientes acima do aceitavel",
                kind="documentacao",
                severity="media",
                metric_source="metrics_pack.quality.incomplete_description_count",
                evidence=[f"{poor_descriptions} de {total} cards possuem descricao incompleta"],
                impact=3,
                confidence=0.82,
            )
        )

    without_comments = int(communication.get("cards_without_comments") or 0)
    if _ratio(without_comments, total) >= 0.5:
        anomalies.append(
            _item(
                title="Queda de interacao: muitos cards sem comentarios",
                kind="comunicacao",
                severity="media",
                metric_source="metrics_pack.communication.cards_without_comments",
                evidence=[f"{without_comments} de {total} cards nao possuem comentarios"],
                impact=3,
                confidence=0.78,
            )
        )

    stale = int(time.get("stale_cards_7d") or 0)
    if _ratio(stale, total) >= 0.2:
        anomalies.append(
            _item(
                title="Lista operacional pode estar congestionada por cards parados",
                kind="operacional",
                severity="media",
                metric_source="metrics_pack.time.stale_cards_7d",
                evidence=[f"{stale} de {total} cards estao sem atividade ha 7 dias ou mais"],
                impact=3,
                confidence=0.8,
            )
        )

    for member in workload.get("by_member", [])[:5]:
        has_overdue = int(member.get("overdue_count") or 0) > 0
        has_large_sample = total >= 5 and int(member.get("card_count") or 0) >= 4
        if (has_large_sample or has_overdue) and _ratio(int(member.get("card_count") or 0), total) >= 0.5:
            anomalies.append(
                _item(
                    title="Membro sobrecarregado",
                    kind="operacional",
                    severity="alta" if member.get("overdue_count", 0) else "media",
                    metric_source="metrics_pack.workload.by_member",
                    evidence=[
                        f"{member.get('name')} concentra {member.get('card_count')} de {total} cards",
                        f"{member.get('overdue_count', 0)} cards vencidos",
                    ],
                    impact=4,
                    confidence=0.84,
                )
            )
            break

    for risk_group in risks.get("risk_by_activity_type", [])[:3]:
        if total >= 3 and _ratio(int(risk_group.get("count") or 0), total) >= 0.25:
            anomalies.append(
                _item(
                    title=f"Categoria critica: {risk_group.get('name')}",
                    kind="sla",
                    severity="alta",
                    metric_source="metrics_pack.risks.risk_by_activity_type",
                    evidence=[f"{risk_group.get('count')} cards de alto risco em {risk_group.get('name')}"],
                    impact=4,
                    confidence=0.82,
                )
            )
    return _sort_items(anomalies)


def _discover_patterns(metrics: dict[str, Any], cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    volume = metrics.get("volume", {})
    total = int(volume.get("total_cards") or len(cards) or 0)
    if total <= 0:
        return []

    for source, label in (
        ("by_activity_type", "tipo de atividade"),
        ("by_label", "etiqueta"),
        ("by_list", "lista"),
        ("by_status", "status"),
    ):
        rows = volume.get(source, [])
        if not rows:
            continue
        top = rows[0]
        pct = _ratio(int(top.get("count") or 0), total) * 100
        if pct >= 35:
            patterns.append(
                _item(
                    title=f"Concentracao por {label}: {top.get('name')}",
                    kind="pattern",
                    severity="media",
                    metric_source=f"metrics_pack.volume.{source}",
                    evidence=[f"{top.get('count')} de {total} cards ({pct:.1f}%) em {top.get('name')}"],
                    impact=3,
                    confidence=0.78,
                )
            )

    patterns.extend(_trend_patterns(metrics))
    patterns.extend(_text_patterns(cards))
    return _sort_items(patterns)


def _trend_patterns(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    trends = metrics.get("trends", {})
    weekly = trends.get("created_by_week", [])
    if len(weekly) < 2:
        return []
    ordered = list(reversed(weekly))
    previous = int(ordered[-2].get("count") or 0)
    current = int(ordered[-1].get("count") or 0)
    if previous <= 0:
        return []
    change = (current - previous) / previous
    if abs(change) < 0.3:
        return []
    direction = "cresceu" if change > 0 else "caiu"
    return [
        _item(
            title=f"Volume semanal {direction} {abs(change) * 100:.1f}%",
            kind="trend",
            severity="media" if change > 0 else "baixa",
            metric_source="metrics_pack.trends.created_by_week",
            evidence=[
                f"semana anterior={previous}",
                f"semana atual={current}",
            ],
            impact=3 if change > 0 else 2,
            confidence=0.72,
        )
    ]


def _text_patterns(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system_terms = Counter()
    project_terms = Counter()
    for card in cards:
        text = f"{card.get('title', '')}".lower()
        for match in re.findall(r"sistema\s+([a-z0-9_-]+)", text):
            system_terms[match] += 1
        for match in re.findall(r"projeto\s+([a-z0-9_-]+)", text):
            project_terms[match] += 1
    patterns = []
    for label, counter in (("sistema", system_terms), ("projeto", project_terms)):
        if counter:
            name, count = counter.most_common(1)[0]
            if count >= 2:
                patterns.append(
                    _item(
                        title=f"{label.title()} recorrente: {name}",
                        kind="pattern",
                        severity="baixa",
                        metric_source=f"activity_classification.cards.title:{label}",
                        evidence=[f"{count} cards citam {label} {name}"],
                        impact=2,
                        confidence=0.65,
                    )
                )
    return patterns


def _discover_correlations(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(cards) < MIN_CORRELATION_SAMPLE:
        return []

    datasets = {
        "descricao_pobre": [1 if c.get("description_quality_score", 0) < 50 else 0 for c in cards],
        "sem_comentarios": [1 if c.get("comment_count", 0) == 0 else 0 for c in cards],
        "checklist_pendente": [1 if c.get("checklist_pending", 0) > 0 else 0 for c in cards],
        "alto_risco": [1 if c.get("risk_score", 0) >= 60 else 0 for c in cards],
        "parado_7d": [1 if c.get("stale_days") is not None and c.get("stale_days") >= 7 else 0 for c in cards],
    }
    candidates = [
        ("descricao_pobre", "alto_risco", "Descricoes pobres aparecem associadas a maior risco"),
        ("sem_comentarios", "parado_7d", "Poucos comentarios aparecem associados a cards parados"),
        ("checklist_pendente", "alto_risco", "Checklists pendentes aparecem associados a maior risco"),
        ("sem_comentarios", "alto_risco", "Ausencia de interacao aparece associada a maior risco"),
    ]
    correlations = []
    for left, right, title in candidates:
        coeff = _phi(datasets[left], datasets[right])
        if coeff is None or abs(coeff) < 0.3:
            continue
        correlations.append(
            {
                "title": title,
                "coefficient": round(coeff, 3),
                "sample": len(cards),
                "confidence": round(min(0.9, 0.55 + abs(coeff) * 0.35 + min(len(cards), 20) / 100), 2),
                "metric_source": f"activity_classification.cards.{left}__{right}",
                "evidence": [
                    f"{left}=1 em {sum(datasets[left])} cards",
                    f"{right}=1 em {sum(datasets[right])} cards",
                    f"coeficiente_phi={coeff:.3f}",
                ],
                "limitations": [
                    "Correlacao nao implica causalidade.",
                    "Amostra baseada somente no recorte filtrado do relatorio.",
                ],
            }
        )
    return sorted(correlations, key=lambda item: abs(item["coefficient"]), reverse=True)


def _build_hotspots(metrics: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    volume = metrics.get("volume", {})
    workload = metrics.get("workload", {})
    risks = metrics.get("risks", {})
    return {
        "top_categories": _top(volume.get("by_label", [])),
        "top_members": _top(workload.get("by_member", []), name_key="name", count_key="card_count"),
        "top_systems": _terms(cards, r"sistema\s+([a-z0-9_-]+)"),
        "top_projects": _terms(cards, r"projeto\s+([a-z0-9_-]+)"),
        "top_types": _top(volume.get("by_activity_type", [])),
        "top_risks": risks.get("high_risk_cards", [])[:10],
        "top_bottlenecks": _top(volume.get("by_list", [])),
    }


def _detect_opportunities(
    metrics: dict[str, Any],
    cards: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    volume = metrics.get("volume", {})
    quality = metrics.get("quality", {})
    communication = metrics.get("communication", {})

    for activity in volume.get("by_activity_type", [])[:3]:
        if int(activity.get("count") or 0) >= 3:
            opportunities.append(
                _opportunity(
                    title=f"Playbook candidato para {activity.get('name')}",
                    evidence=[f"{activity.get('count')} cards do tipo {activity.get('name')}"],
                    potential_gain="Reduzir variacao de execucao em demandas recorrentes.",
                    recommended_action="Criar checklist padrao e criterio de triagem para esta categoria.",
                    confidence=0.76,
                )
            )

    if quality.get("incomplete_description_count"):
        opportunities.append(
            _opportunity(
                title="Automacao de qualidade de descricao",
                evidence=[f"{quality['incomplete_description_count']} cards com descricao incompleta"],
                potential_gain="Aumentar explicabilidade e reduzir retrabalho por falta de contexto.",
                recommended_action="Adicionar checklist minimo de descricao antes de mover para execucao.",
                confidence=0.82,
            )
        )

    if communication.get("cards_without_comments"):
        opportunities.append(
            _opportunity(
                title="Rotina de follow-up automatico para cards sem interacao",
                evidence=[f"{communication['cards_without_comments']} cards sem comentarios"],
                potential_gain="Reduzir cards parados e melhorar rastreabilidade de decisao.",
                recommended_action="Criar lembrete operacional para cards sem comentario apos periodo definido.",
                confidence=0.74,
            )
        )

    duplicate_groups = _similar_cards(cards)
    if duplicate_groups:
        opportunities.append(
            _opportunity(
                title="Possiveis duplicidades ou cards semelhantes",
                evidence=[f"{len(group)} cards semelhantes: {', '.join(group[:5])}" for group in duplicate_groups[:2]],
                potential_gain="Reduzir retrabalho e consolidar demandas repetidas.",
                recommended_action="Revisar grupos semelhantes e consolidar quando forem o mesmo problema.",
                confidence=0.68,
            )
        )

    if correlations:
        opportunities.append(
            _opportunity(
                title="Intervencao orientada por correlacao",
                evidence=correlations[0]["evidence"],
                potential_gain="Atacar um fator associado ao risco observado.",
                recommended_action=correlations[0]["title"],
                confidence=correlations[0]["confidence"],
            )
        )
    return opportunities[:10]


def _build_highlights(
    anomalies: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
    hotspots: dict[str, Any],
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    highlights = []
    for item in anomalies[:5]:
        highlights.append({**item, "source": "anomaly"})
    for item in patterns[:3]:
        highlights.append({**item, "source": "pattern"})
    for item in correlations[:2]:
        highlights.append(
            {
                "title": item["title"],
                "kind": "correlation",
                "severity": "media",
                "metric_source": item["metric_source"],
                "evidence": item["evidence"],
                "impact": 3,
                "confidence": item["confidence"],
                "source": "correlation",
            }
        )
    for item in opportunities[:3]:
        highlights.append(
            {
                "title": item["title"],
                "kind": "opportunity",
                "severity": "media",
                "metric_source": "discovery.opportunities",
                "evidence": item["evidence"],
                "impact": 3,
                "confidence": item["confidence"],
                "source": "opportunity",
            }
        )
    for risk in hotspots.get("top_risks", [])[:2]:
        highlights.append(
            {
                "title": f"Hotspot de risco: {risk.get('card_id')}",
                "kind": "hotspot",
                "severity": "alta",
                "metric_source": "discovery.hotspots.top_risks",
                "evidence": risk.get("reasons") or [f"risk_score={risk.get('risk_score')}"],
                "impact": 4,
                "confidence": 0.8,
                "source": "hotspot",
            }
        )
    return _sort_items(highlights)[:10]


def _build_surprises(metrics: dict[str, Any], cards: list[dict[str, Any]], hotspots: dict[str, Any]) -> list[dict[str, Any]]:
    surprises: list[dict[str, Any]] = []
    total = int(metrics.get("volume", {}).get("total_cards") or len(cards) or 0)
    if total <= 0:
        return []

    categories = hotspots.get("top_categories", [])
    if len(categories) >= 2:
        top_two = sum(int(item.get("count") or 0) for item in categories[:2])
        pct = _ratio(top_two, total) * 100
        if pct >= 60:
            surprises.append(
                _surprise(
                    text=f"{pct:.1f}% dos cards concentram-se em apenas duas categorias.",
                    evidence=[f"{categories[0]['name']}={categories[0]['count']}", f"{categories[1]['name']}={categories[1]['count']}"],
                    impact=4,
                    confidence=0.82,
                )
            )

    comments = [(card.get("card_id"), int(card.get("comment_count") or 0)) for card in cards]
    total_comments = sum(count for _, count in comments)
    if total_comments > 0 and len(comments) >= 4:
        top_comment_cards = sorted(comments, key=lambda item: item[1], reverse=True)
        top_count = max(1, math.ceil(len(comments) * 0.2))
        top_comments = sum(count for _, count in top_comment_cards[:top_count])
        pct_comments = _ratio(top_comments, total_comments) * 100
        if pct_comments >= 60:
            pct_cards = _ratio(top_count, len(comments)) * 100
            surprises.append(
                _surprise(
                    text=f"{pct_cards:.1f}% dos cards concentram {pct_comments:.1f}% dos comentarios.",
                    evidence=[f"top_cards={top_count}", f"top_comments={top_comments}", f"total_comments={total_comments}"],
                    impact=3,
                    confidence=0.78,
                )
            )
    return surprises[:10]


def _build_forecast(
    metrics: dict[str, Any],
    anomalies: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    forecasts: list[dict[str, Any]] = []
    trends = metrics.get("trends", {})
    weekly = trends.get("created_by_week", [])
    if len(weekly) >= 2:
        ordered = list(reversed(weekly))
        previous = int(ordered[-2].get("count") or 0)
        current = int(ordered[-1].get("count") or 0)
        if previous > 0 and current > previous:
            forecasts.append(
                {
                    "scenario": "Se o ritmo atual continuar, o backlog tende a crescer.",
                    "confidence": 0.72,
                    "basis": [f"semana anterior={previous}", f"semana atual={current}"],
                    "trend_observed": True,
                }
            )
    if any(item["metric_source"] == "metrics_pack.sla.overdue_open_cards" for item in anomalies):
        forecasts.append(
            {
                "scenario": "Risco crescente de rompimento de SLA se os cards vencidos nao forem replanejados.",
                "confidence": 0.76,
                "basis": [
                    evidence
                    for item in anomalies
                    if item["metric_source"] == "metrics_pack.sla.overdue_open_cards"
                    for evidence in item["evidence"]
                ],
                "trend_observed": True,
            }
        )
    if any(item.get("kind") == "trend" and "cresceu" in item.get("title", "") for item in patterns):
        forecasts.append(
            {
                "scenario": "Tendencia de aumento de entrada operacional no recorte recente.",
                "confidence": 0.7,
                "basis": [e for item in patterns if item.get("kind") == "trend" for e in item.get("evidence", [])],
                "trend_observed": True,
            }
        )
    return [item for item in forecasts if item.get("basis")]


def _score_report_intelligence(
    *,
    anomalies: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    correlations: list[dict[str, Any]],
    hotspots: dict[str, Any],
    opportunities: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
    surprises: list[dict[str, Any]],
    forecast: list[dict[str, Any]],
    analytical: dict[str, Any],
    executive_narrative: dict[str, Any],
) -> dict[str, Any]:
    coverage = analytical.get("quality", {}).get("report_quality_score", 0)
    readability = executive_narrative.get("executive_readability_score", {}).get("score", 0)
    populated_hotspots = sum(1 for value in hotspots.values() if value)
    score = min(
        100,
        min(20, len(highlights) * 2)
        + min(15, len(anomalies) * 3)
        + min(15, len(patterns) * 2)
        + min(15, len(correlations) * 5)
        + min(10, len(surprises) * 5)
        + min(10, len(forecast) * 5)
        + min(10, len(opportunities) * 2)
        + min(5, populated_hotspots)
        + (coverage / 100 * 5)
        + (readability / 100 * 5),
    )
    rounded = round(score, 1)
    return {
        "score": rounded,
        "label": "excelente" if rounded >= 85 else "bom" if rounded >= 70 else "regular" if rounded >= 50 else "baixo",
        "components": {
            "insights": len(highlights),
            "correlations": len(correlations),
            "anomalies": len(anomalies),
            "discoveries": len(surprises),
            "trends": len(forecast),
            "recommendations": len(opportunities),
            "coverage": coverage,
            "explainability": readability,
        },
        "justification": [
            f"{len(highlights)} destaques executivos",
            f"{len(anomalies)} anomalias com evidencia",
            f"{len(correlations)} correlacoes com amostra minima",
            f"{len(surprises)} descobertas suportadas por dados",
        ],
    }


def _item(
    *,
    title: str,
    kind: str,
    severity: str,
    metric_source: str,
    evidence: list[str],
    impact: int,
    confidence: float,
) -> dict[str, Any]:
    return {
        "title": title,
        "kind": kind,
        "severity": severity,
        "metric_source": metric_source,
        "evidence": [str(item) for item in evidence if str(item)],
        "impact": impact,
        "confidence": round(confidence, 2),
    }


def _opportunity(
    *,
    title: str,
    evidence: list[str],
    potential_gain: str,
    recommended_action: str,
    confidence: float,
) -> dict[str, Any]:
    return {
        "title": title,
        "evidence": [str(item) for item in evidence if str(item)],
        "potential_gain": potential_gain,
        "recommended_action": recommended_action,
        "confidence": round(confidence, 2),
    }


def _surprise(*, text: str, evidence: list[str], impact: int, confidence: float) -> dict[str, Any]:
    return {
        "text": text,
        "evidence": evidence,
        "impact": impact,
        "confidence": round(confidence, 2),
    }


def _sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_weight = {"critica": 4, "alta": 3, "media": 2, "baixa": 1}
    return sorted(
        items,
        key=lambda item: (
            int(item.get("impact") or 0),
            severity_weight.get(item.get("severity"), 0),
            float(item.get("confidence") or 0),
        ),
        reverse=True,
    )


def _top(rows: list[dict[str, Any]], *, name_key: str = "name", count_key: str = "count") -> list[dict[str, Any]]:
    normalized = [
        {"name": item.get(name_key), "count": item.get(count_key, 0), **item}
        for item in rows
        if item.get(name_key)
    ]
    return sorted(normalized, key=lambda item: int(item.get("count") or 0), reverse=True)[:10]


def _terms(cards: list[dict[str, Any]], pattern: str) -> list[dict[str, Any]]:
    counter = Counter()
    for card in cards:
        for match in re.findall(pattern, str(card.get("title", "")).lower()):
            counter[match] += 1
    return [{"name": name, "count": count} for name, count in counter.most_common(10)]


def _similar_cards(cards: list[dict[str, Any]]) -> list[list[str]]:
    groups: dict[str, list[str]] = {}
    for card in cards:
        words = [
            word
            for word in re.findall(r"[a-z0-9]{4,}", str(card.get("title", "")).lower())
            if word not in {"card", "para", "com", "sem", "ajustar"}
        ]
        if not words:
            continue
        key = " ".join(sorted(words[:3]))
        groups.setdefault(key, []).append(card.get("card_id"))
    return [ids for ids in groups.values() if len(ids) >= 2]


def _phi(left: list[int], right: list[int]) -> float | None:
    if len(left) != len(right) or len(left) < MIN_CORRELATION_SAMPLE:
        return None
    n11 = sum(1 for a, b in zip(left, right) if a == 1 and b == 1)
    n10 = sum(1 for a, b in zip(left, right) if a == 1 and b == 0)
    n01 = sum(1 for a, b in zip(left, right) if a == 0 and b == 1)
    n00 = sum(1 for a, b in zip(left, right) if a == 0 and b == 0)
    denominator = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denominator == 0:
        return None
    return (n11 * n00 - n10 * n01) / denominator


def _ratio(part: int, total: int) -> float:
    return part / total if total else 0.0
