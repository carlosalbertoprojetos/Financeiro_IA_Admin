class AIConfigurationError(Exception):
    """Raised when OpenAI credentials or settings are missing."""


class AIAnalysisError(Exception):
    """Raised when OpenAI analysis fails or returns invalid data."""
