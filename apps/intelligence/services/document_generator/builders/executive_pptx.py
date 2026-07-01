from __future__ import annotations

from apps.intelligence.services.document_generator.builders.ooxml import xml_escape, zip_bytes
from apps.intelligence.services.document_generator.presentation import PresentationModel


def build_executive_pptx(model: PresentationModel) -> bytes:
    slides = _slides(model)
    files = {
        "[Content_Types].xml": _content_types(len(slides)),
        "_rels/.rels": _root_rels(),
        "ppt/presentation.xml": _presentation(len(slides)),
        "ppt/_rels/presentation.xml.rels": _presentation_rels(len(slides)),
        "ppt/theme/theme1.xml": _theme(),
    }
    for index, slide in enumerate(slides, start=1):
        files[f"ppt/slides/slide{index}.xml"] = _slide_xml(slide["title"], slide["bullets"])
        files[f"ppt/slides/_rels/slide{index}.xml.rels"] = _empty_rels()
    return zip_bytes(files)


def _slides(model: PresentationModel) -> list[dict[str, list[str] | str]]:
    return [
        {"title": "Capa", "bullets": [model.title, model.subtitle, model.branding.confidentiality]},
        {"title": "Executive Brief", "bullets": _brief(model)},
        {"title": "Operational Scorecard", "bullets": [f"Score operacional: {model.scorecard.get('score_operacional', 'N/A')}"]},
        {"title": "KPIs", "bullets": [f"{item.get('metrica')}: {item.get('valor')} ({item.get('status')})" for item in model.kpis[:5]]},
        {"title": "Top 3 Drivers", "bullets": [item.get("title") or item.get("name") for item in model.rankings.get("top_10_causes", [])[:3]]},
        {"title": "Gargalos", "bullets": [f"{item.get('lista_etapa')}: {item.get('cards')} cards" for item in model.tables.get("gargalos", [])[:4]]},
        {"title": "Riscos", "bullets": [item.get("title") for item in model.risks[:4]]},
        {"title": "Oportunidades", "bullets": [item.get("title") for item in model.rankings.get("top_10_opportunities", [])[:4]]},
        {"title": "Decisões", "bullets": [item.get("decisao") for item in model.decisions[:4]]},
        {"title": "Plano de Ação", "bullets": [item.get("acao") for item in model.action_plan[:4]]},
        {"title": "Próximos Passos", "bullets": [item.get("acao") for item in model.action_plan[:3]] or ["Revisar evidencias e executar decisoes priorizadas."]},
        {"title": "Encerramento", "bullets": [model.branding.footer, f"Versao {model.branding.version}"]},
    ]


def _brief(model: PresentationModel) -> list[str]:
    brief = model.executive_brief
    return [
        f"Status: {brief.get('status_geral', 'N/A')}",
        f"Score: {brief.get('score_operacional', 'N/A')}",
        brief.get("summary", ""),
    ]


def _slide_xml(title: str, bullets: list[str]) -> str:
    bullet_xml = "".join(
        f"<a:p><a:r><a:rPr lang=\"pt-BR\" sz=\"1800\"/><a:t>{xml_escape(item)}</a:t></a:r></a:p>"
        for item in bullets
        if item
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
        f'{_text_box(2, "Title", 609600, 457200, 7924800, 762000, title, 3200)}'
        f'{_body_box(3, "Body", 914400, 1524000, 7772400, 4572000, bullet_xml)}'
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )


def _text_box(shape_id: int, name: str, x: int, y: int, cx: int, cy: int, text: str, size: int) -> str:
    return (
        "<p:sp>"
        f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p><a:r><a:rPr lang="pt-BR" sz="{size}" b="1"/><a:t>{xml_escape(text)}</a:t></a:r></a:p></p:txBody>'
        "</p:sp>"
    )


def _body_box(shape_id: int, name: str, x: int, y: int, cx: int, cy: int, body: str) -> str:
    return (
        "<p:sp>"
        f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{body}</p:txBody>'
        "</p:sp>"
    )


def _presentation(slide_count: int) -> str:
    ids = "".join(f'<p:sldId id="{255 + index}" r:id="rId{index}"/>' for index in range(1, slide_count + 1))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f"<p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx=\"9144000\" cy=\"6858000\" type=\"screen4x3\"/>"
        "</p:presentation>"
    )


def _presentation_rels(slide_count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{index}.xml"/>'
        for index in range(1, slide_count + 1)
    )
    rels += f'<Relationship Id="rId{slide_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    return f'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>'


def _content_types(slide_count: int) -> str:
    slides = "".join(
        f'<Override PartName="/ppt/slides/slide{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for index in range(1, slide_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        f"{slides}</Types>"
    )


def _root_rels() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
        "</Relationships>"
    )


def _empty_rels() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'


def _theme() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="EOR">'
        "<a:themeElements><a:clrScheme name=\"EOR\"><a:dk1><a:srgbClr val=\"111827\"/></a:dk1>"
        "<a:lt1><a:srgbClr val=\"FFFFFF\"/></a:lt1><a:accent1><a:srgbClr val=\"2563EB\"/></a:accent1>"
        "</a:clrScheme><a:fontScheme name=\"EOR\"><a:majorFont><a:latin typeface=\"Aptos\"/></a:majorFont>"
        "<a:minorFont><a:latin typeface=\"Aptos\"/></a:minorFont></a:fontScheme><a:fmtScheme name=\"EOR\"/>"
        "</a:themeElements></a:theme>"
    )
