"""Shared wiring for API and worker composition roots."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .adapters.ai.cached_evaluator import CachedEvaluator
from .adapters.ai.gemma_ollama import GemmaOllamaAdapter
from .adapters.ai.metered_evaluator import MeteredEvaluator
from .adapters.broker.rabbitmq_adapter import RabbitMQAdapter
from .adapters.cache.in_memory_cache import InMemoryCache
from .adapters.db.engine import create_engine, create_session_factory
from .adapters.db.postgres_job_repository import PostgresJobRepository
from .adapters.db.postgres_study_repository import PostgresStudyRepository
from .adapters.metrics.jsonl_metrics import JsonlMetrics
from .adapters.scrapers.pmc import PMCAdapter
from .adapters.system.clock import SystemClock
from .adapters.system.logger import ConsoleLogger
from .application.use_cases.evaluate_study import EvaluateStudyUseCase
from .application.use_cases.get_job import GetJobUseCase
from .application.use_cases.process_evaluation_job import ProcessEvaluationJobUseCase
from .application.use_cases.submit_evaluation import SubmitEvaluationUseCase
from .config import Settings
from .domain.ports.evaluator import EvaluatorPort
from .domain.ports.logger import LoggerPort
from .domain.ports.metrics import MetricsPort


class AppContainer:
    def __init__(self, settings: Settings, *, correlation_id: str | None = None) -> None:
        self.settings = settings
        self.engine: AsyncEngine = create_engine(settings)
        self.session_factory: async_sessionmaker[AsyncSession] = create_session_factory(self.engine)
        self.logger: LoggerPort = ConsoleLogger(correlation_id=correlation_id or "app")
        self.clock = SystemClock()
        self.metrics: MetricsPort = JsonlMetrics()
        self.study_repository = PostgresStudyRepository(self.session_factory, logger=self.logger)
        self.job_repository = PostgresJobRepository(self.session_factory)
        self.queue = RabbitMQAdapter(
            settings.rabbitmq_url,
            queue_name=settings.rabbitmq_evaluation_queue,
            logger=self.logger,
        )
        self.ingestor = PMCAdapter(logger=self.logger)
        self.evaluator = self._build_evaluator()
        self.evaluate_study = EvaluateStudyUseCase(
            ingestor=self.ingestor,
            evaluator=self.evaluator,
            repository=self.study_repository,
            logger=self.logger,
            clock=self.clock,
            metrics=self.metrics,
        )
        self.submit_evaluation = SubmitEvaluationUseCase(
            jobs=self.job_repository,
            queue=self.queue,
            clock=self.clock,
            logger=self.logger,
            idempotency_window=timedelta(hours=settings.evaluation_idempotency_hours),
        )
        self.get_job = GetJobUseCase(
            jobs=self.job_repository,
            studies=self.study_repository,
        )
        self.process_evaluation_job = ProcessEvaluationJobUseCase(
            evaluate=self.evaluate_study,
            jobs=self.job_repository,
            clock=self.clock,
            logger=self.logger,
        )

    def _build_evaluator(self) -> EvaluatorPort:
        base = GemmaOllamaAdapter(logger=self.logger)
        metered: EvaluatorPort = MeteredEvaluator(
            base,
            metrics=self.metrics,
            model=base.model_tag,
        )
        return CachedEvaluator(
            metered,
            InMemoryCache(),
            model_tag=base.model_tag,
        )

    async def startup(self) -> None:
        await self.queue.connect()

    async def shutdown(self) -> None:
        await self.queue.close()
        if isinstance(self.ingestor, PMCAdapter):
            await self.ingestor.aclose()
        await self.engine.dispose()
