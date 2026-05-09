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
        Phase 1 end-to-end evaluation workflow:
        Wires Ingestor -> Evaluator -> Scorer -> Repository.
        """
        log = self.logger.with_context(study_id=study_id)
        log.info("evaluation_started")

        # 1. Ingest
        try:
            raw_text = await self.ingestor.fetch_by_id(study_id)
            log.info("ingestion_completed", length=len(raw_text))
        except Exception as e:
            log.error("ingestion_failed", exc=e)
            raise

        # 2. Evaluate
        try:
            study = await self.evaluator.evaluate_text(raw_text)
            study.id = study_id
            log.info("evaluation_completed")
        except Exception as e:
            log.error("evaluation_failed", exc=e)
            raise

        # 3. Score
        try:
            scoring_result = self.scorer.calculate_rigor_index(study)
            study.score = scoring_result.score
            study.confidence = scoring_result.confidence
            study.quality_tier = scoring_result.quality_tier
            study.score_breakdown = scoring_result.score_breakdown
            study.scraped_at = self.clock.now()
            log.info("scoring_completed", score=study.score, tier=study.quality_tier)
        except Exception as e:
            log.error("scoring_failed", exc=e)
            raise

        # 4. Persist
        try:
            await self.repository.save(study)
            log.info("persistence_completed")
        except Exception as e:
            log.error("persistence_failed", exc=e)
            raise

        log.info("evaluation_succeeded")
        return study
