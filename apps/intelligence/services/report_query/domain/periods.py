from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import NamedTuple

from django.utils import timezone

from apps.intelligence.services.report_query.domain.filters import PeriodPreset


class DateRange(NamedTuple):
    start: datetime
    end: datetime


def resolve_period(
    *,
    preset: PeriodPreset | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    reference: datetime | None = None,
) -> DateRange | None:
    """Resolve a period preset or custom range into timezone-aware datetimes."""
    now = reference or timezone.now()
    today = timezone.localdate(now)

    if preset == PeriodPreset.CUSTOM or (date_from and date_to):
        start = _parse_date(date_from, end_of_day=False)
        end = _parse_date(date_to, end_of_day=True)
        if start and end:
            return DateRange(start=start, end=end)
        return None

    if preset is None:
        return None

    if preset == PeriodPreset.TODAY:
        return DateRange(
            start=timezone.make_aware(datetime.combine(today, time.min)),
            end=now,
        )

    if preset == PeriodPreset.YESTERDAY:
        yesterday = today - timedelta(days=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(yesterday, time.min)),
            end=timezone.make_aware(datetime.combine(yesterday, time.max)),
        )

    days_map = {
        PeriodPreset.LAST_7_DAYS: 7,
        PeriodPreset.LAST_15_DAYS: 15,
        PeriodPreset.LAST_30_DAYS: 30,
        PeriodPreset.LAST_90_DAYS: 90,
    }
    if preset in days_map:
        days = days_map[preset]
        start_date = today - timedelta(days=days - 1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(start_date, time.min)),
            end=now,
        )

    if preset == PeriodPreset.THIS_MONTH:
        start_date = today.replace(day=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(start_date, time.min)),
            end=now,
        )

    if preset == PeriodPreset.PREVIOUS_MONTH:
        first_this_month = today.replace(day=1)
        last_prev = first_this_month - timedelta(days=1)
        first_prev = last_prev.replace(day=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(first_prev, time.min)),
            end=timezone.make_aware(datetime.combine(last_prev, time.max)),
        )

    if preset == PeriodPreset.QUARTER:
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(start_date, time.min)),
            end=now,
        )

    if preset == PeriodPreset.SEMESTER:
        semester_start_month = 1 if today.month <= 6 else 7
        start_date = today.replace(month=semester_start_month, day=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(start_date, time.min)),
            end=now,
        )

    if preset == PeriodPreset.YEAR:
        start_date = today.replace(month=1, day=1)
        return DateRange(
            start=timezone.make_aware(datetime.combine(start_date, time.min)),
            end=now,
        )

    return None


def _parse_date(value: str | None, *, end_of_day: bool) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(value.strip(), fmt).date()
            t = time.max if end_of_day else time.min
            return timezone.make_aware(datetime.combine(parsed, t))
        except ValueError:
            continue
    return None
