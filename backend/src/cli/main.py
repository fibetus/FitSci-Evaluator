import argparse
import asyncio
import sys

from ..adapters.ai.gemma_ollama import GemmaOllamaAdapter
from ..adapters.db.in_memory_repository import InMemoryStudyRepository
from ..adapters.scrapers.pmc import PMCAdapter
from ..adapters.system.clock import SystemClock
from ..adapters.system.logger import ConsoleLogger
from ..application.use_cases.evaluate_study import EvaluateStudyUseCase
from ..domain.models.study import Population, Study
from ..domain.services.scoring import ScoringService


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="FitSci Evaluator CLI")
    parser.add_argument("id", help="PMC ID to evaluate (e.g. PMC12345)")
    parser.add_argument("--mock", action="store_true", help="Use legacy mock offline mode")
    args = parser.parse_args()

    print(f"[*] Starting evaluation for {args.id}...")

    if args.mock:
        # MOCK DATA (Simulating Ingestor + Sifter)
        mock_study = Study(
            id=args.id,
            pmc_url=f"https://pmc.ncbi.nlm.nih.gov/articles/{args.id}/",
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
            )
        )
        scoring_result = ScoringService.calculate_rigor_index(mock_study)
        mock_study.score = scoring_result.score
        mock_study.confidence = scoring_result.confidence
        mock_study.quality_tier = scoring_result.quality_tier
        mock_study.score_breakdown = scoring_result.score_breakdown
        study = mock_study
    else:
        # REAL PIPELINE
        ingestor = PMCAdapter()
        evaluator = GemmaOllamaAdapter()
        repository = InMemoryStudyRepository()
        logger = ConsoleLogger()
        clock = SystemClock()

        use_case = EvaluateStudyUseCase(
            ingestor=ingestor,
            evaluator=evaluator,
            repository=repository,
            logger=logger,
            clock=clock,
            scorer=ScoringService,
        )

        try:
            study = await use_case.execute(args.id)
        except Exception as e:
            print(f"\n[!] Evaluation failed: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            await ingestor.aclose()

    # OUTPUT
    print("\n" + "="*50)
    print(f"VERDICT: {study.quality_tier.upper()}")
    print(f"SCORE: {study.score}/14 ({study.confidence}%)")
    print("="*50)
    print(f"Title: {study.title}")
    print(f"Journal: {study.journal} (IF: {study.impact_factor})")
    print(f"Type: {study.type.upper()}")
    print("-"*50)
    print(f"Breakdown: {study.score_breakdown.model_dump()}")
    print("="*50 + "\n")


def run() -> None:
    asyncio.run(async_main())

if __name__ == "__main__":
    run()
