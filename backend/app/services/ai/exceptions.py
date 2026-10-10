"""
RELIEFOS Lite — AI Infrastructure Exception Hierarchy
Typed exceptions for provider interactions, security guards, and rate limits.
"""


class AIError(Exception):
    """Base class for all RELIEFOS Lite AI exceptions."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AIProviderError(AIError):
    """Raised when an external model provider returns an unrecoverable error."""
    pass


class AIAuthenticationError(AIProviderError):
    """Raised when provider credentials (API key) are invalid or rejected."""
    pass


class AIRateLimitError(AIError):
    """Raised when client or provider rate limits are exceeded."""
    pass


class AITimeoutError(AIError):
    """Raised when provider fails to return within the statutory timeout threshold."""
    pass


class AIParsingError(AIError):
    """Raised when LLM output cannot be structured into the compliant schema."""
    pass


class AIPromptSecurityError(AIError):
    """Raised when user input contains adversarial prompt injection patterns."""
    pass
