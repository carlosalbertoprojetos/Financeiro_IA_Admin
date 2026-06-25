"""EQL validator tests."""

from __future__ import annotations

from django.test import TestCase

from apps.intelligence.services.eql.ast import EQLQuery
from apps.intelligence.services.eql.errors import (
    InvalidFieldError,
    InvalidOperatorError,
    MissingBoardIdError,
    MissingLimitError,
)
from apps.intelligence.services.eql.validator import validate_eql


class EQLValidatorTests(TestCase):
    def _base(self) -> EQLQuery:
        return EQLQuery(type="EXECUTIVE", board_id="b1", limit=100)

    def test_valid_query(self) -> None:
        q = self._base()
        q.metrics = ["LEAD_TIME", "RISK_SCORE"]
        q.group_by = ["LABELS"]
        validated = validate_eql(q)
        self.assertEqual(validated.limit, 100)

    def test_invalid_field_metric(self) -> None:
        q = self._base()
        q.metrics = ["INVALID_METRIC"]
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_group_by(self) -> None:
        q = self._base()
        q.group_by = ["UNKNOWN"]
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_sort_field(self) -> None:
        from apps.intelligence.services.eql.ast import SortSpec

        q = self._base()
        q.sort = [SortSpec("BAD_FIELD", "DESC")]
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_sort_order(self) -> None:
        from apps.intelligence.services.eql.ast import SortSpec

        q = self._base()
        q.sort = [SortSpec("RISK_SCORE", "SIDEWAYS")]  # type: ignore[arg-type]
        with self.assertRaises(InvalidOperatorError):
            validate_eql(q)

    def test_missing_board_id(self) -> None:
        q = self._base()
        q.board_id = ""
        with self.assertRaises(MissingBoardIdError):
            validate_eql(q)

    def test_missing_limit(self) -> None:
        q = self._base()
        q.limit = 0
        with self.assertRaises(MissingLimitError):
            validate_eql(q)

    def test_limit_exceeds_max(self) -> None:
        q = self._base()
        q.limit = 5000
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_report_type(self) -> None:
        q = self._base()
        q.type = "UNKNOWN"
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_filter_field(self) -> None:
        q = self._base()
        q.filters = {"bad_field": "x"}
        with self.assertRaises(InvalidFieldError):
            validate_eql(q)

    def test_invalid_comparison_operator(self) -> None:
        q = self._base()
        q.filters = {"risk_score": {"op": "!=", "value": 10}}
        with self.assertRaises(InvalidOperatorError):
            validate_eql(q)
