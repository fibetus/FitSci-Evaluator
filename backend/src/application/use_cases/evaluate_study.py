import time
from dataclasses import dataclass

from src.domain.errors import (
    ExtractionError,
    FitSciError,
    IngestionError,
    RepositoryError,
    ScoringError,
)
from src.domain.models.study import Study
from src.domain.ports.clock import ClockPort
from src.domain.ports.evaluator import EvaluatorPort
from src.domain.ports.ingestor import IngestorPort
from src.domain.ports.logger import LoggerPort
from src.domain.ports.metrics import MetricsPort
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
    metrics: MetricsPort | None = None

    async def execute(self, study_id: str) -> Study:
        """
        Phase 1 end-to-end evaluation workflow:
        Wires Ingestor -> Evaluator -> Scorer -> Repository.
        """
        started = time.perf_counter()
        log = self.logger.with_context(study_id=study_id)
        log.info("evaluation_started")

        try:
            raw_text = await self.ingestor.fetch_by_id(study_id)
            log.info("ingestion_completed", length=len(raw_text))
        except IngestionError:
            log.error("ingestion_failed")
            raise
        except Exception as exc:
            log.error("ingestion_failed", exc=exc)
            raise IngestionError("Unexpected error during ingestion") from exc

        try:
            extraction = await self.evaluator.evaluate_text(raw_text)
            study = extraction.into_study(study_id=study_id)
            log.info("evaluation_completed")
        except ExtractionError:
            log.error("evaluation_failed")
            raise
        except Exception as exc:
            log.error("evaluation_failed", exc=exc)
            raise ExtractionError("Unexpected error during evaluation") from exc

        try:
            scoring_result = self.scorer.calculate_rigor_index(study)
            study = study.model_copy(
                update={
                    "score": scoring_result.score,
                    "confidence": scoring_result.confidence,
                    "quality_tier": scoring_result.quality_tier,
                    "score_breakdown": scoring_result.score_breakdown,
                    "scraped_at": self.clock.now(),
                }
            )
            log.info("scoring_completed", score=study.score, tier=study.quality_tier)
        except FitSciError:
            log.error("scoring_failed")
            raise
        except Exception as exc:
            log.error("scoring_failed", exc=exc)
            raise ScoringError("Unexpected error during scoring") from exc

        try:
            await self.repository.save(study)
            log.info("persistence_completed")
        except RepositoryError:
            log.error("persistence_failed")
            raise
        except Exception as exc:
            log.error("persistence_failed", exc=exc)
            raise RepositoryError("Unexpected error during persistence") from exc

        total_latency_ms = int((time.perf_counter() - started) * 1000)
        if self.metrics is not None:
            try:
                self.metrics.record_evaluation(
                    study_id=study_id,
                    score=study.score,
                    quality_tier=study.quality_tier,
                    confidence=study.confidence,
                    total_latency_ms=total_latency_ms,
                )
            except Exception as exc:
                log.warning("metrics_recording_failed", exception=str(exc))

        log.info("evaluation_succeeded", total_latency_ms=total_latency_ms)
        return study
