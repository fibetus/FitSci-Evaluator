import argparse
import asyncio
import sys
import uuid

from ..adapters.ai.cached_evaluator import CachedEvaluator
from ..adapters.ai.gemma_ollama import GemmaOllamaAdapter
from ..adapters.ai.metered_evaluator import MeteredEvaluator
from ..adapters.ai.mock import MockEvaluatorAdapter
from ..adapters.cache.in_memory_cache import InMemoryCache
from ..adapters.db.in_memory_repository import InMemoryStudyRepository
from ..adapters.metrics.jsonl_metrics import JsonlMetrics
from ..adapters.scrapers.mock_ingestor import MockIngestorAdapter
from ..adapters.scrapers.pmc import PMCAdapter
from ..adapters.system.clock import SystemClock
from ..adapters.system.logger import ConsoleLogger
from ..application.use_cases.evaluate_study import EvaluateStudyUseCase
from ..domain.ports.evaluator import EvaluatorPort
from ..domain.ports.ingestor import IngestorPort
from ..domain.ports.logger import LoggerPort
from ..domain.ports.metrics import MetricsPort
from ..domain.services.scoring import ScoringService


def _build_evaluator(*, logger: LoggerPort, metrics: MetricsPort) -> EvaluatorPort:
    base = GemmaOllamaAdapter(logger=logger)
    cached: EvaluatorPort = CachedEvaluator(
        base,
        InMemoryCache(),
        model_tag=base.model_tag,
    )
    return MeteredEvaluator(cached, metrics=metrics, model=base.model_tag)


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="FitSci Evaluator CLI")
    parser.add_argument("id", help="PMC ID to evaluate (e.g. PMC12345)")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use offline mock adapters (no network/Ollama)",
    )
    args = parser.parse_args()

    correlation_id = uuid.uuid4().hex
    logger = ConsoleLogger(correlation_id=correlation_id)
    clock = SystemClock()
    metrics = JsonlMetrics()
    repository = InMemoryStudyRepository(logger=logger)

    print(f"[*] Starting evaluation for {args.id}...")

    ingestor: IngestorPort
    evaluator: EvaluatorPort
    if args.mock:
        ingestor = MockIngestorAdapter()
        evaluator = MockEvaluatorAdapter()
    else:
        ingestor = PMCAdapter(logger=logger)
        evaluator = _build_evaluator(logger=logger, metrics=metrics)

    use_case = EvaluateStudyUseCase(
        ingestor=ingestor,
        evaluator=evaluator,
        repository=repository,
        logger=logger,
        clock=clock,
        scorer=ScoringService,
        metrics=metrics,
    )

    try:
        study = await use_case.execute(args.id)
    except Exception as exc:
        print(f"\n[!] Evaluation failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        if isinstance(ingestor, PMCAdapter):
            await ingestor.aclose()

    print("\n" + "=" * 50)
    print(f"VERDICT: {study.quality_tier.upper()}")
    print(f"SCORE: {study.score}/14 ({study.confidence}%)")
    print("=" * 50)
    print(f"Title: {study.title}")
    print(f"Journal: {study.journal} (IF: {study.impact_factor})")
    print(f"Type: {study.type.upper()}")
    print("-" * 50)
    print(f"Breakdown: {study.score_breakdown.model_dump()}")
    print("=" * 50 + "\n")


def run() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    run()
