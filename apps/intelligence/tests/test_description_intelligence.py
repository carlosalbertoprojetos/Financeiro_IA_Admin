from django.test import SimpleTestCase

from apps.intelligence.services.description_intelligence.summary import analyze_description


DESCRIPTION = """
# Incidente de infraestrutura

Objetivo: Restabelecer acesso ao sistema ERP.
Cliente: ACME
Sistema: ERP Financeiro
Ambiente: produção
Problema: servidor srv-db-01 indisponível no IP 10.0.0.15.
Ticket: INC-12345

- Análise realizada nos logs app.log
- Ação executada: rollback da versão v2.4.1
- Teste realizado com usuário financeiro
- Resultado obtido: serviço normalizado

URL: https://status.example.com/inc/12345
"""


class DescriptionIntelligenceTests(SimpleTestCase):
    def test_extracts_structured_knowledge_with_traceability(self) -> None:
        result = analyze_description(DESCRIPTION)

        self.assertEqual(result["expanded_summary"]["objetivo"]["line"], 4)
        self.assertEqual(result["expanded_summary"]["problema"]["line"], 8)
        self.assertTrue(result["classifications"])
        self.assertTrue(all("confidence" in item for item in result["classifications"]))

    def test_extracts_entities_and_events(self) -> None:
        result = analyze_description(DESCRIPTION)
        entities = {(item["entity_type"], item["value"]) for item in result["entities"]}
        events = {item["event_type"] for item in result["events"]}

        self.assertIn(("ip", "10.0.0.15"), entities)
        self.assertIn(("ticket", "INC-12345"), entities)
        self.assertIn(("host", "srv-db-01"), entities)
        self.assertIn("ANALYSIS_PERFORMED", events)
        self.assertIn("ACTION_EXECUTED", events)
        self.assertIn("RESULT_RECORDED", events)

    def test_quality_and_kpis_are_computed(self) -> None:
        result = analyze_description(DESCRIPTION)

        self.assertGreaterEqual(result["quality"]["score"], 60)
        self.assertGreater(result["kpis"]["infrastructure_workload_index"], 0)
        self.assertGreater(result["kpis"]["operational_complexity_score"], 0)

    def test_empty_description_does_not_infer_facts(self) -> None:
        result = analyze_description("")

        self.assertEqual(result["expanded_summary"]["objetivo"], None)
        self.assertEqual(result["entities"], [])
        self.assertEqual(result["events"], [])
        self.assertEqual(result["classifications"][0]["category"], "Outra")
