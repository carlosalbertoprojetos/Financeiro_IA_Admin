from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.integrations.trello.mapper import map_card_to_task
from apps.intelligence.services.description_intelligence.structured_sections import (
    compute_documentation_completeness,
    parse_structured_description,
)
from apps.intelligence.services.report_query.engine.post_processor import _card_base_row
from apps.intelligence.services.trello_card_intelligence import normalize_trello_card


COMPLETE_DESCRIPTION = """
Data da Solicitação:
2026-06-20

OBJETIVO
Reduzir atraso dos relatórios executivos.

CONTEXTO
Board com 12 cards atrasados e risco de SLA em 48h.

ATIVIDADES
- Mapear cards sem responsável
- Revisar checklist operacional

RESULTADO ESPERADO
Relatório gerencial publicado com 95% de cobertura.

RISCOS
- Dados incompletos
- Falta de evidências

Critérios de conclusão:
1. PDF gerado
2. Dashboard revisado

Resultado obtido
Relatório validado pela operação.

Evidências
- https://example.com/evidencia
- print anexado no card
"""


class StructuredDescriptionParserTests(SimpleTestCase):
    def test_complete_description_returns_contract_shape(self) -> None:
        parsed = parse_structured_description(COMPLETE_DESCRIPTION)

        self.assertEqual(parsed["data_solicitacao"], "2026-06-20")
        self.assertIn("Reduzir atraso", parsed["objetivo"])
        self.assertEqual(parsed["atividades"], ["Mapear cards sem responsável", "Revisar checklist operacional"])
        self.assertEqual(parsed["riscos"], ["Dados incompletos", "Falta de evidências"])
        self.assertEqual(parsed["criterios_conclusao"], ["PDF gerado", "Dashboard revisado"])
        self.assertEqual(parsed["evidencias"], ["https://example.com/evidencia", "print anexado no card"])
        self.assertIn("https://example.com/evidencia", parsed["links"])
        self.assertIn("95%", parsed["metricas"])
        self.assertIn("12 cards", parsed["metricas"])
        self.assertEqual(parsed["raw_description"].strip(), COMPLETE_DESCRIPTION.strip())

    def test_incomplete_description_keeps_missing_values_empty(self) -> None:
        parsed = parse_structured_description("Objetivo: Corrigir relatório\nRisco: prazo curto")

        self.assertEqual(parsed["objetivo"], "Corrigir relatório")
        self.assertEqual(parsed["riscos"], ["prazo curto"])
        self.assertIsNone(parsed["contexto"])
        self.assertEqual(parsed["atividades"], [])
        self.assertEqual(parsed["evidencias"], [])

    def test_heading_variations_are_supported(self) -> None:
        parsed = parse_structured_description(
            """
            Objetivos:
            Padronizar cards
            Resultado Esperado:
            Menos retrabalho
            Critério de Conclusão
            Checklist fechado
            Evidência
            Link no card
            """
        )

        self.assertEqual(parsed["objetivo"], "Padronizar cards")
        self.assertEqual(parsed["resultado_esperado"], "Menos retrabalho")
        self.assertEqual(parsed["criterios_conclusao"], ["Checklist fechado"])
        self.assertEqual(parsed["evidencias"], ["Link no card"])

    def test_free_text_and_empty_description_do_not_infer_sections(self) -> None:
        free_text = parse_structured_description("Card urgente com 2 pendências. Ver https://example.com")
        empty = parse_structured_description("")

        self.assertIsNone(free_text["objetivo"])
        self.assertEqual(free_text["atividades"], [])
        self.assertEqual(free_text["links"], ["https://example.com"])
        self.assertEqual(free_text["metricas"], ["2"])
        self.assertEqual(empty["raw_description"], "")
        self.assertIsNone(empty["objetivo"])
        self.assertEqual(empty["links"], [])


class TrelloCardNormalizerTests(SimpleTestCase):
    def test_normalizes_card_without_database_dependency(self) -> None:
        card = _fake_card(description=COMPLETE_DESCRIPTION)
        action = SimpleNamespace(
            action_type="commentCard",
            raw_json={"data": {"card": {"id": "card-1"}, "text": "feito"}},
        )

        normalized = normalize_trello_card(card, actions=[action]).to_dict()

        self.assertEqual(normalized["id"], "card-1")
        self.assertEqual(normalized["name"], "Relatório executivo")
        self.assertEqual(normalized["list_name"], "Doing")
        self.assertEqual(normalized["checklist_total"], 3)
        self.assertEqual(normalized["checklist_completed"], 2)
        self.assertEqual(normalized["checklist_completion_percent"], 66.7)
        self.assertEqual(normalized["comments_count"], 1)
        self.assertEqual(normalized["attachments_count"], 2)
        self.assertEqual(normalized["risks_count"], 2)
        self.assertEqual(normalized["evidences_count"], 2)
        self.assertGreaterEqual(normalized["documentation_completeness_score"], 90)

    def test_documentation_completeness_respects_missing_checklist_and_owner(self) -> None:
        parsed = parse_structured_description("Objetivo: Revisar card")

        score = compute_documentation_completeness(parsed, has_checklist=False, has_owner=False)

        self.assertEqual(score, 10)


class TrelloReportIntegrationTests(SimpleTestCase):
    def test_canonical_mapper_preserves_old_fields_and_adds_description_metadata(self) -> None:
        task = map_card_to_task(
            {
                "id": "card-1",
                "name": "Relatório executivo",
                "desc": "Objetivo: Melhorar relatório\nEvidências\n- https://example.com",
                "idList": "list-1",
                "due": None,
                "dueComplete": False,
                "closed": False,
                "labels": [{"id": "label-1", "name": "Alta", "color": "red"}],
                "badges": {"checkItems": 4, "checkItemsCheck": 3},
                "url": "https://trello.com/c/card-1",
            },
            project={"id": "board-1", "name": "Board", "url": "https://trello.com/b/board-1"},
            list_by_id={"list-1": {"id": "list-1", "name": "Doing"}},
            workspace_id="workspace-1",
        )

        self.assertEqual(task.source_provider, "trello")
        self.assertEqual(task.source_id, "card-1")
        self.assertEqual(task.title, "Relatório executivo")
        self.assertEqual(task.status, "Doing")
        self.assertEqual(task.metadata["labels"][0]["name"], "Alta")
        self.assertEqual(task.metadata["checklist_total"], 4)
        self.assertEqual(task.metadata["checklist_completion_percent"], 75.0)
        self.assertEqual(task.metadata["description_sections"]["objetivo"], "Melhorar relatório")
        self.assertEqual(task.metadata["evidences_count"], 1)

    def test_report_card_row_keeps_old_keys_and_adds_structured_fields(self) -> None:
        row = _card_base_row(_fake_card(description=COMPLETE_DESCRIPTION))

        self.assertEqual(row["card_id"], "card-1")
        self.assertEqual(row["title"], "Relatório executivo")
        self.assertEqual(row["status"], "Doing")
        self.assertEqual(row["labels"], ["Alta"])
        self.assertEqual(row["assignees"], ["Ana"])
        self.assertIn("description_sections", row)
        self.assertIn("documentation_completeness_score", row)
        self.assertEqual(row["description_risks_count"], 2)
        self.assertEqual(row["checklist_total"], 3)


def _fake_card(*, description: str) -> SimpleNamespace:
    return SimpleNamespace(
        trello_id="card-1",
        title="Relatório executivo",
        description=description,
        status="Doing",
        board_list=SimpleNamespace(name="Doing"),
        created_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        due_at=None,
        completed_at=None,
        labels=[{"id": "label-1", "name": "Alta", "color": "red"}],
        raw_json={
            "badges": {"checkItems": 3, "checkItemsCheck": 2, "attachments": 2},
        },
        assignees=_FakeRelated(
            [
                SimpleNamespace(trello_id="member-1", full_name="Ana", username="ana"),
            ]
        ),
    )


class _FakeRelated:
    def __init__(self, values: list[SimpleNamespace]) -> None:
        self._values = values

    def all(self) -> list[SimpleNamespace]:
        return self._values

