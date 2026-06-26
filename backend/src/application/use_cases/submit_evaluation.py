from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from src.domain.errors import QueueError, RepositoryError
from src.domain.models.job import EvaluationJob
from src.domain.ports.clock import ClockPort
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.logger import LoggerPort
from src.domain.ports.message_queue import MessageQueuePort


@dataclass(frozen=True)
class SubmitEvaluationUseCase:
    jobs: JobRepositoryPort
    queue: MessageQueuePort
    clock: ClockPort
    logger: LoggerPort
    idempotency_window: timedelta = timedelta(hours=24)

    async def execute(self, pmc_id: str) -> EvaluationJob:
        log = self.logger.with_context(pmc_id=pmc_id)
        existing = await self.jobs.find_recent_by_pmc_id(
            pmc_id,
            within=self.idempotency_window,
        )
        if existing is not None and existing.status != "failed":
            log.info("evaluation_job_idempotent_hit", job_id=existing.id)
            return existing

        now = self.clock.now()
        job = EvaluationJob.new(job_id=uuid.uuid4().hex, pmc_id=pmc_id, now=now)
        try:
            await self.jobs.save(job)
        except RepositoryError:
            log.error("evaluation_job_save_failed", job_id=job.id)
            raise

        try:
            await self.queue.publish_evaluation_job(job.id, pmc_id)
        except QueueError as exc:
            log.error("evaluation_job_publish_failed", job_id=job.id)
            try:
                await self.jobs.update_status(
                    job.id,
                    "failed",
                    error_message=str(exc),
                    updated_at=self.clock.now(),
                )
            except RepositoryError:
                log.error("evaluation_job_mark_failed_failed", job_id=job.id)
            raise

        log.info("evaluation_job_submitted", job_id=job.id)
        return job
