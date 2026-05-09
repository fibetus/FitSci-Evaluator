import json
import sys
from typing import Any

from ...domain.ports.logger import LoggerPort


class ConsoleLogger(LoggerPort):
    def __init__(self, **context: Any):
        self._context = context

    def info(self, event: str, **fields: Any) -> None:
        self._log("INFO", event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._log("WARNING", event, **fields)

    def error(self, event: str, exc: Exception | None = None, **fields: Any) -> None:
        if exc is not None:
            fields["exception"] = str(exc)
        self._log("ERROR", event, **fields)

    def with_context(self, **fields: Any) -> "LoggerPort":
        new_context = self._context.copy()
        new_context.update(fields)
        return ConsoleLogger(**new_context)

    def _log(self, level: str, event: str, **fields: Any) -> None:
        payload = {"level": level, "event": event, **self._context, **fields}
        print(json.dumps(payload), file=sys.stderr)
