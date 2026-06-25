from __future__ import annotations


class EQLError(Exception):
    code: str = "EQL_ERROR"

    def __init__(self, message: str, *, code: str | None = None, line: int | None = None) -> None:
        self.message = message
        self.code = code or self.code
        self.line = line
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "line": self.line}


class SyntaxError(EQLError):
    code = "SYNTAX_ERROR"


class InvalidFieldError(EQLError):
    code = "INVALID_FIELD"


class InvalidOperatorError(EQLError):
    code = "INVALID_OPERATOR"


class MissingLimitError(EQLError):
    code = "MISSING_LIMIT"


class MissingReportTypeError(EQLError):
    code = "MISSING_REPORT_TYPE"


class MissingBoardIdError(EQLError):
    code = "MISSING_BOARD_ID"


class QueryTimeoutError(EQLError):
    code = "QUERY_TIMEOUT"


class QueryLimitExceededError(EQLError):
    code = "QUERY_LIMIT_EXCEEDED"


class QueryGuardRejectedError(EQLError):
    code = "QUERY_GUARD_REJECTED"


class QueryCostRejectedError(EQLError):
    code = "QUERY_COST_REJECTED"
