from __future__ import annotations

import html
import zipfile
from io import BytesIO
from typing import Iterable


def xml_escape(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def zip_bytes(files: dict[str, str | bytes]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path, content in files.items():
            data = content.encode("utf-8") if isinstance(content, str) else content
            package.writestr(path, data)
    return buffer.getvalue()


def paragraph(text: object) -> str:
    return f"<w:p><w:r><w:t>{xml_escape(text)}</w:t></w:r></w:p>"


def docx_table(headers: list[str], rows: Iterable[list[object]]) -> str:
    def cell(value: object) -> str:
        return f"<w:tc>{paragraph(value)}</w:tc>"

    xml = ["<w:tbl>"]
    xml.append("<w:tr>" + "".join(cell(header) for header in headers) + "</w:tr>")
    for row in rows:
        xml.append("<w:tr>" + "".join(cell(value) for value in row) + "</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)
