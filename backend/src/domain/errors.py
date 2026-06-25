class FitSciError(Exception):
    """Base class for FitSci domain and application errors."""


class IngestionError(FitSciError):
    """Raised when an ingestor cannot fetch or parse a source document."""


class ExtractionError(FitSciError):
    """Raised when an evaluator cannot produce schema-valid extraction output."""


class ScoringError(FitSciError):
    """Raised when study scoring fails outside evaluator extraction concerns."""


class ValidationError(FitSciError):
    """Raised when validated domain data cannot satisfy application invariants."""


class RepositoryError(FitSciError):
    """Raised when a repository cannot persist or retrieve evaluations."""


class ConfigurationError(FitSciError):
    """Raised when startup configuration is missing or invalid."""


class QueueError(FitSciError):
    """Raised when a message broker cannot publish or consume messages."""


class JobNotFoundError(FitSciError):
    """Raised when a job record does not exist."""
