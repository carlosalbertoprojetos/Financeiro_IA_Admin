from __future__ import annotations


class GovernanceError(Exception):
    code: str = "GOVERNANCE_ERROR"

    def __init__(self, message: str, *, code: str | None = None, details: dict | None = None) -> None:
        self.message = message
        self.code = code or self.code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class UnregisteredEntityError(GovernanceError):
    code = "UNREGISTERED_ENTITY"


class UnregisteredMetricError(GovernanceError):
    code = "UNREGISTERED_METRIC"


class UnregisteredEventError(GovernanceError):
    code = "UNREGISTERED_EVENT"


class SemanticInconsistencyError(GovernanceError):
    code = "SEMANTIC_INCONSISTENCY"


class ModelVersionError(GovernanceError):
    code = "MODEL_VERSION_ERROR"


class CrossLayerValidationError(GovernanceError):
    code = "CROSS_LAYER_VALIDATION"
