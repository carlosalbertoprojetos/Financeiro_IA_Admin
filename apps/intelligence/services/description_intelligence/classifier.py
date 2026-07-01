from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from apps.intelligence.services.description_intelligence.parser import Evidence, ParsedDescription


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
        }


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Infraestrutura": ("infra", "servidor", "rede", "backup", "storage", "datacenter", "firewall"),
    "Correção": ("correção", "corrigir", "ajuste corretivo", "hotfix"),
    "Bug": ("bug", "defeito", "erro", "falha"),
    "Incidente": ("incidente", "indisponível", "queda", "impacto", "sev", "p1", "p2"),
    "Solicitação": ("solicitação", "pedido", "requisitado", "demanda"),
    "Atendimento": ("atendimento", "suporte", "chamado", "usuário"),
    "Reparo": ("reparo", "conserto", "substituição"),
    "Ajuste": ("ajuste", "alterar", "corrigir parâmetro"),
    "Melhoria": ("melhoria", "otimização", "evolução"),
    "Feature": ("feature", "funcionalidade", "nova tela", "novo recurso"),
    "Projeto": ("projeto", "sprint", "entrega", "milestone"),
    "Mudança": ("mudança", "change", "rfc"),
    "Deploy": ("deploy", "implantação", "publicação", "release"),
    "Atualização": ("atualização", "upgrade", "patch"),
    "Configuração": ("configuração", "parametrização", "setup"),
    "Banco de Dados": ("banco", "database", "sql", "postgres", "mysql", "oracle"),
    "Rede": ("rede", "dns", "vpn", "ip", "latência", "roteador"),
    "Servidor": ("servidor", "host", "vm", "cpu", "memória"),
    "Backup": ("backup", "restore", "snapshot"),
    "Segurança": ("segurança", "vulnerabilidade", "permissão", "acesso", "token"),
    "Monitoramento": ("monitoramento", "alerta", "observabilidade", "log"),
    "Integração": ("integração", "api", "webhook", "conector"),
    "Automação": ("automação", "script", "job", "pipeline"),
    "Documentação": ("documentação", "manual", "procedimento"),
    "Treinamento": ("treinamento", "capacitação", "orientação"),
    "Preventiva": ("preventiva", "prevenção", "antes da falha"),
    "Corretiva": ("corretiva", "corrigir", "após falha"),
}


def classify_description(parsed: ParsedDescription) -> list[ClassificationResult]:
    """Classify description into multiple operational categories with evidence."""
    text = parsed.normalized_text.lower()
    scores: Counter[str] = Counter()
    evidence_by_category: dict[str, list[Evidence]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() not in text:
                continue
            matched = _evidence_for_keyword(parsed.lines, keyword)
            scores[category] += max(1, len(matched))
            evidence_by_category.setdefault(category, []).extend(matched[:3])

    if not scores:
        return [ClassificationResult(category="Outra", confidence=0.25, evidence=parsed.lines[:1])]

    max_score = max(scores.values())
    results = [
        ClassificationResult(
            category=category,
            confidence=round(min(0.98, 0.45 + (score / max_score) * 0.45), 2),
            evidence=_dedupe_evidence(evidence_by_category.get(category, [])),
        )
        for category, score in scores.most_common()
    ]
    return results


def _evidence_for_keyword(lines: list[Evidence], keyword: str) -> list[Evidence]:
    pattern = re.compile(re.escape(keyword), re.I)
    return [line for line in lines if pattern.search(line.evidence)]


def _dedupe_evidence(items: list[Evidence]) -> list[Evidence]:
    seen: set[tuple[str, int, str]] = set()
    unique: list[Evidence] = []
    for item in items:
        key = (item.source, item.line, item.evidence)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
