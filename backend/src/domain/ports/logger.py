from typing import Any, Protocol


class LoggerPort(Protocol):
    def info(self, event: str, **fields: Any) -> None:
        """Record an informational event."""
        ...

    def warning(self, event: str, **fields: Any) -> None:
        """Record a warning event."""
        ...

    def error(
        self,
        event: str,
        exc: Exception | None = None,
        **fields: Any,
    ) -> None:
        """Record an error event."""
        ...

    def with_context(self, **fields: Any) -> "LoggerPort":
        """Return a logger enriched with persistent context fields."""
        ...
