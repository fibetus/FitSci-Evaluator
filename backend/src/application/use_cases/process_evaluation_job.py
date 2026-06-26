from __future__ import annotations

from dataclasses import dataclass

from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.errors import (
    ExtractionError,
    IngestionError,
    RepositoryError,
    ScoringError,
    ValidationError,
)
from src.domain.ports.clock import ClockPort
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.logger import LoggerPort


@dataclass(frozen=True)
class ProcessEvaluationJobUseCase:
    evaluate: EvaluateStudyUseCase
    jobs: JobRepositoryPort
    clock: ClockPort
    logger: LoggerPort

    async def execute(self, job_id: str, pmc_id: str) -> None:
        log = self.logger.with_context(job_id=job_id, pmc_id=pmc_id)
        await self.jobs.update_status(
            job_id,
            "running",
            updated_at=self.clock.now(),
        )
        log.info("evaluation_job_running")

        try:
            await self.evaluate.execute(pmc_id)
        except (IngestionError, ExtractionError, ScoringError, ValidationError) as exc:
            await self.jobs.update_status(
                job_id,
                "failed",
                error_message=str(exc),
                updated_at=self.clock.now(),
            )
            log.error("evaluation_job_failed", exc=exc)
            return
        except RepositoryError as exc:
            await self.jobs.update_status(
                job_id,
                "pending",
                updated_at=self.clock.now(),
            )
            log.error("evaluation_job_transient_failure", exc=exc)
            raise
        except Exception as exc:
            await self.jobs.update_status(
                job_id,
                "pending",
                updated_at=self.clock.now(),
            )
            log.error("evaluation_job_transient_failure", exc=exc)
            raise

        await self.jobs.update_status(
            job_id,
            "succeeded",
            updated_at=self.clock.now(),
        )
        log.info("evaluation_job_succeeded")
