from __future__ import annotations


class DriftEngineError(Exception):
    """Base exception for drift engine failures."""


class CollectorError(DriftEngineError):
    """Raised when a collector cannot obtain state."""


class BaselineValidationError(DriftEngineError):
    """Raised when a baseline is invalid or has been tampered with."""


class BaselineNotFoundError(DriftEngineError):
    """Raised when a requested baseline cannot be found."""


class PolicyEvaluationError(DriftEngineError):
    """Raised when policy evaluation fails."""


class RemediationError(DriftEngineError):
    """Raised when remediation planning or execution fails."""


class StorageError(DriftEngineError):
    """Raised when persistence operations fail."""
