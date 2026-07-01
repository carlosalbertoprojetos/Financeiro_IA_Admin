from __future__ import annotations

from django.test import SimpleTestCase

from apps.integrations.services.task_persistence import canonical_task_from_payload
from apps.integrations.trello.mapper import map_trello_payload


class CanonicalEquivalenceTests(SimpleTestCase):
    def test_trello_mapper_represents_legacy_card_facts(self) -> None:
        payload = _trello_payload()

        task = map_trello_payload(payload, workspace_id="org-1")[0]
        legacy_facts = _legacy_facts()

        self.assertEqual(task.source_id, legacy_facts["card_id"])
        self.assertEqual(task.title, legacy_facts["title"])
        self.assertEqual(task.status, legacy_facts["list_name"])
        self.assertEqual(task.description, legacy_facts["description"])
        self.assertEqual(task.assignees[0]["id"], legacy_facts["assignee_id"])
        self.assertEqual(task.labels[0]["name"], legacy_facts["label"])
        self.assertEqual(task.comments[0]["text"], legacy_facts["comment"])
        self.assertEqual(task.movements[0]["from_list"]["name"], "To Do")
        self.assertEqual(task.movements[0]["to_list"]["name"], "Doing")
        self.assertEqual(len(task.actions), legacy_facts["actions_count"])
        self.assertEqual(len(task.attachments), legacy_facts["attachments_count"])
        self.assertEqual(task.derived_fields["checklist_total"], legacy_facts["checklist_total"])
        self.assertEqual(task.derived_fields["checklist_completed"], legacy_facts["checklist_completed"])
        self.assertEqual(task.derived_fields["comments_count"], legacy_facts["comments_count"])
        self.assertEqual(task.derived_fields["movements_count"], legacy_facts["movements_count"])
        self.assertEqual(task.derived_fields["documentation_completeness_score"], 100)

    def test_canonical_payload_roundtrip_keeps_rich_fields(self) -> None:
        task = map_trello_payload(_trello_payload(), workspace_id="org-1")[0]

        rebuilt = canonical_task_from_payload(task.as_dict())

        self.assertEqual(rebuilt.source_id, task.source_id)
        self.assertEqual(rebuilt.assignees, task.assignees)
        self.assertEqual(rebuilt.comments, task.comments)
        self.assertEqual(rebuilt.movements, task.movements)
        self.assertEqual(rebuilt.checklists, task.checklists)
        self.assertEqual(rebuilt.attachments, task.attachments)
        self.assertEqual(rebuilt.derived_fields["comments_count"], 1)
        self.assertEqual(rebuilt.metadata["derived_fields"]["movements_count"], 1)

    def test_documented_engine_equivalence_boundaries(self) -> None:
        task = map_trello_payload(_trello_payload(), workspace_id="org-1")[0]

        equivalence = {
            "metrics": bool(task.derived_fields),
            "events": bool(task.actions),
            "risks": bool(task.structured_description.get("riscos")),
            "classification": bool(task.description or task.labels),
            "narrative": False,
            "discovery": False,
            "decisions": False,
        }

        self.assertTrue(equivalence["metrics"])
        self.assertTrue(equivalence["events"])
        self.assertTrue(equivalence["risks"])
        self.assertTrue(equivalence["classification"])
        self.assertFalse(equivalence["narrative"])
        self.assertFalse(equivalence["discovery"])
        self.assertFalse(equivalence["decisions"])


def _legacy_facts() -> dict[str, object]:
    return {
        "card_id": "card-1",
        "title": "Relatorio executivo",
        "list_name": "Doing",
        "description": _description(),
        "assignee_id": "member-1",
        "label": "Alta",
        "comment": "Validado com a operacao.",
        "actions_count": 2,
        "attachments_count": 1,
        "checklist_total": 2,
        "checklist_completed": 1,
        "comments_count": 1,
        "movements_count": 1,
    }


def _trello_payload() -> dict[str, object]:
    return {
        "board": {
            "id": "board-1",
            "name": "Board",
            "url": "https://trello.com/b/board-1",
            "closed": False,
            "idOrganization": "org-1",
        },
        "lists": [
            {"id": "list-1", "name": "To Do", "pos": 1},
            {"id": "list-2", "name": "Doing", "pos": 2},
        ],
        "members": [
            {"id": "member-1", "username": "ana", "fullName": "Ana"},
            {"id": "member-2", "username": "bruno", "fullName": "Bruno"},
        ],
        "cards": [
            {
                "id": "card-1",
                "name": "Relatorio executivo",
                "desc": _description(),
                "idList": "list-2",
                "idMembers": ["member-1"],
                "idMembersWatching": ["member-2"],
                "due": "2026-06-30T12:00:00.000Z",
                "dueComplete": False,
                "closed": False,
                "dateLastActivity": "2026-06-28T10:00:00.000Z",
                "labels": [{"id": "label-1", "name": "Alta", "color": "red"}],
                "badges": {"checkItems": 2, "checkItemsCheck": 1},
                "attachments": [
                    {
                        "id": "att-1",
                        "name": "evidencia.png",
                        "url": "https://example.com/evidencia.png",
                    }
                ],
                "url": "https://trello.com/c/card-1",
            }
        ],
        "actions": [
            {
                "id": "action-1",
                "type": "updateCard",
                "date": "2026-06-27T10:00:00.000Z",
                "idMemberCreator": "member-1",
                "data": {
                    "card": {"id": "card-1"},
                    "listBefore": {"id": "list-1", "name": "To Do", "pos": 1},
                    "listAfter": {"id": "list-2", "name": "Doing", "pos": 2},
                },
            },
            {
                "id": "action-2",
                "type": "commentCard",
                "date": "2026-06-28T10:00:00.000Z",
                "idMemberCreator": "member-2",
                "data": {
                    "card": {"id": "card-1"},
                    "text": "Validado com a operacao.",
                },
            },
        ],
    }


def _description() -> str:
    return """
Objetivo: Consolidar relatorio
Contexto: Board executivo
Atividades
- Revisar dados
Resultado esperado: Relatorio confiavel
Risco: Dados incompletos
Criterio de conclusao: Evidencia anexada
Resultado obtido: Validado
Evidencias
- https://example.com/evidencia.png
"""

