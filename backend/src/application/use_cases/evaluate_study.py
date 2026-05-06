from dataclasses import dataclass

from src.domain.models.study import Study
from src.domain.ports.clock import ClockPort
from src.domain.ports.evaluator import EvaluatorPort
from src.domain.ports.ingestor import IngestorPort
from src.domain.ports.logger import LoggerPort
from src.domain.ports.repository import RepositoryPort
from src.domain.services.scoring import ScoringService


@dataclass(frozen=True)
class EvaluateStudyUseCase:
    ingestor: IngestorPort
    evaluator: EvaluatorPort
    repository: RepositoryPort
    logger: LoggerPort
    clock: ClockPort
    scorer: type[ScoringService] = ScoringService

    async def execute(self, study_id: str) -> Study:
        """
        Phase 0 skeleton for the Phase 1 end-to-end evaluation workflow.

        Phase 1 will wire Ingestor -> Evaluator -> Scorer -> Repository here.
        """
        raise NotImplementedError(
            f"EvaluateStudyUseCase.execute({study_id!r}) is implemented in Phase 1."
        )
