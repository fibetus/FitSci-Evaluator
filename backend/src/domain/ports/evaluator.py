from typing import Protocol

from ..models.study import Study


class EvaluatorPort(Protocol):
    async def evaluate_text(self, text: str) -> Study:
        """
        Takes raw text from a publication and uses Gemma 4 
        to extract structured data matching the Study model.
        """
        ...
