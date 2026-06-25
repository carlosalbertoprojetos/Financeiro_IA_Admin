from __future__ import annotations

import re
from typing import Pattern

from apps.intelligence.services.report_query.domain.filters import TitleFilter, TitleMatchMode

PREFIX_PATTERN = re.compile(r"\[([^\]]+)\]")
STRUCTURED_PREFIXES = frozenset(
    {"AQUI", "FINANCEIRO", "CLIENTE", "URGENTE", "PROJETO", "RH", "COMERCIAL", "JURIDICO", "JURÍDICO", "OPERACAO", "OPERAÇÃO"}
)


def extract_prefix(title: str) -> str | None:
    """Extract the first structured prefix from a card title."""
    match = PREFIX_PATTERN.search(title or "")
    if not match:
        return None
    return match.group(1).strip().upper()


def extract_all_prefixes(title: str) -> list[str]:
    """Extract all bracket prefixes from a title."""
    return [m.group(1).strip().upper() for m in PREFIX_PATTERN.finditer(title or "")]


def parse_structured_title(title: str) -> dict[str, str | None]:
    """
    Parse structured title like '[AQUI] Revisar Contrato XPTO'.

    Returns category (prefix) and clean title without prefix.
    """
    prefix = extract_prefix(title)
    clean = PREFIX_PATTERN.sub("", title or "").strip()
    clean = re.sub(r"\s+", " ", clean)
    return {"category": prefix, "clean_title": clean or title}


def title_matches(filter_spec: TitleFilter, title: str) -> bool:
    """Check if a card title matches the title filter specification."""
    if filter_spec.prefix:
        prefixes = extract_all_prefixes(title)
        if filter_spec.prefix.upper() not in prefixes:
            return False

    value = filter_spec.value
    if not value:
        return True

    haystack = title or ""
    mode = filter_spec.mode

    if mode == TitleMatchMode.CONTAINS:
        return value.lower() in haystack.lower()
    if mode == TitleMatchMode.NOT_CONTAINS:
        return value.lower() not in haystack.lower()
    if mode == TitleMatchMode.STARTS_WITH:
        return haystack.lower().startswith(value.lower())
    if mode == TitleMatchMode.ENDS_WITH:
        return haystack.lower().endswith(value.lower())
    if mode == TitleMatchMode.REGEX:
        try:
            return bool(re.search(value, haystack, re.IGNORECASE))
        except re.error:
            return False
    return True


def compile_title_filter(
    title_contains: str = "",
    title_prefix: str = "",
    title_filter: TitleFilter | None = None,
) -> TitleFilter:
    """Build a unified TitleFilter from payload fields."""
    if title_filter:
        if title_prefix and not title_filter.prefix:
            title_filter.prefix = title_prefix
        if title_contains and not title_filter.value:
            title_filter.value = title_contains
        return title_filter

    return TitleFilter(
        mode=TitleMatchMode.CONTAINS,
        value=title_contains,
        prefix=title_prefix,
    )
