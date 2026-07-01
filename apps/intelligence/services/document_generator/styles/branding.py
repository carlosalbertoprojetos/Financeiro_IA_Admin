from __future__ import annotations

from typing import Any

from apps.intelligence.services.document_generator.presentation import BrandingConfig


def normalize_branding(data: dict[str, Any] | None = None) -> BrandingConfig:
    values = data or {}
    return BrandingConfig(
        company=str(values.get("company") or "EOR"),
        client=str(values.get("client") or ""),
        confidentiality=str(values.get("confidentiality") or "Confidencial"),
        version=str(values.get("version") or "1.0"),
        footer=str(values.get("footer") or "Executive Operation Report"),
        header=str(values.get("header") or "Executive Document"),
        logo_path=str(values.get("logo_path") or ""),
        primary_color=str(values.get("primary_color") or "#0F172A"),
        secondary_color=str(values.get("secondary_color") or "#2563EB"),
        accent_color=str(values.get("accent_color") or "#F59E0B"),
    )
