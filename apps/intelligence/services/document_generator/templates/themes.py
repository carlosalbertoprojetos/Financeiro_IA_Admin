from __future__ import annotations

from apps.intelligence.services.document_generator.presentation import Theme


THEMES = {
    "corporate": Theme(
        name="corporate",
        primary_color="#0F172A",
        secondary_color="#2563EB",
        background_color="#FFFFFF",
        text_color="#111827",
        muted_color="#64748B",
        risk_color="#DC2626",
    ),
    "minimal": Theme(
        name="minimal",
        primary_color="#111827",
        secondary_color="#6B7280",
        background_color="#FFFFFF",
        text_color="#111827",
        muted_color="#9CA3AF",
        risk_color="#B91C1C",
    ),
    "executive": Theme(
        name="executive",
        primary_color="#111827",
        secondary_color="#1D4ED8",
        background_color="#F8FAFC",
        text_color="#111827",
        muted_color="#475569",
        risk_color="#B91C1C",
    ),
    "dark": Theme(
        name="dark",
        primary_color="#020617",
        secondary_color="#38BDF8",
        background_color="#0F172A",
        text_color="#E5E7EB",
        muted_color="#94A3B8",
        risk_color="#F87171",
    ),
}


def get_theme(name: str = "corporate") -> Theme:
    return THEMES.get((name or "corporate").lower(), THEMES["corporate"])
