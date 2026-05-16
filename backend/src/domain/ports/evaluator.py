from typing import Protocol

from ..models.extraction import ExtractionResult


class EvaluatorPort(Protocol):
    async def evaluate_text(self, text: str) -> ExtractionResult:
        """
        Extract structured methodology fields from raw publication text.
        Scoring fields are owned by the Judge and must not be set here.
        """
        ...
