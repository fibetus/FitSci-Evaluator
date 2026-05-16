from __future__ import annotations

from src.domain.models.extraction import ExtractionResult
from src.domain.models.study import Population
from src.domain.ports.evaluator import EvaluatorPort


class MockEvaluatorAdapter(EvaluatorPort):
    """Returns a fixed extraction for any input (offline CLI / tests)."""

    async def evaluate_text(self, text: str) -> ExtractionResult:
        return ExtractionResult(
            id="PMC00000",
            pmc_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC00000/",
            title="Effect of Resistance Training Volume on Hypertrophy",
            authors=["Schoenfeld B", "et al."],
            journal="Sports Medicine",
            year=2024,
            impact_factor=11.6,
            type="meta-analysis",
            topic="hypertrophy",
            subtopic="volume",
            keywords=["MRI", "Trained", "Meta-analysis"],
            sample_size=450,
            population=Population(training_status="trained", sex="male"),
            primary_outcome="Muscle Thickness",
            summary_en=(
                "High volume training leads to superior hypertrophy "
                "outcomes in trained individuals."
            ),
        )
