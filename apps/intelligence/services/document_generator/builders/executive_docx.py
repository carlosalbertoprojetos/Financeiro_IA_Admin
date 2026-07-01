from __future__ import annotations

from apps.intelligence.services.document_generator.builders.ooxml import docx_table, paragraph, xml_escape, zip_bytes
from apps.intelligence.services.document_generator.presentation import PresentationModel


def build_executive_docx(model: PresentationModel) -> bytes:
    body = [
        paragraph(model.title),
        paragraph(model.subtitle),
        paragraph(model.branding.confidentiality),
        paragraph("Executive Brief"),
        paragraph(model.executive_brief.get("summary", "")),
        paragraph("KPIs"),
        docx_table(
            ["Metrica", "Valor", "Status", "Interpretacao"],
            [[item.get("metrica"), item.get("valor"), item.get("status"), item.get("interpretacao")] for item in model.kpis],
        ),
        paragraph("Decisoes"),
        docx_table(
            ["Decisao", "Evidencia", "Urgencia", "Dono"],
            [[item.get("decisao"), item.get("evidencia"), item.get("urgencia"), item.get("dono_sugerido")] for item in model.decisions],
        ),
        paragraph("Plano de Acao"),
        docx_table(
            ["Acao", "Dono", "Prazo", "Resultado"],
            [[item.get("acao"), item.get("dono"), item.get("prazo"), item.get("resultado_esperado")] for item in model.action_plan],
        ),
        paragraph("Evidencias"),
        *[paragraph(item.get("evidence") or item.get("claim") or item) for item in model.evidence[:30]],
    ]
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}<w:sectPr/></w:body></w:document>"
    )
    return zip_bytes(
        {
            "[Content_Types].xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                "</Types>"
            ),
            "_rels/.rels": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                "</Relationships>"
            ),
            "word/document.xml": document,
            "docProps/core.xml": (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                f"<dc:title>{xml_escape(model.title)}</dc:title></cp:coreProperties>"
            ),
        }
    )
