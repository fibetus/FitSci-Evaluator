import argparse
import asyncio

from ..domain.models.study import Population, Study
from ..domain.services.scoring import ScoringService


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="FitSci Evaluator CLI")
    parser.add_argument("id", help="PMC ID to evaluate (e.g. PMC12345)")
    args = parser.parse_args()

    print(f"[*] Starting evaluation for {args.id}...")

    # MOCK DATA (Simulating Ingestor + Sifter)
    # In a real scenario, we would call ingestor.fetch_by_id and evaluator.evaluate_text
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
            "High volume training leads to superior hypertrophy outcomes in trained individuals."
        )
    )

    # THE JUDGE (Pure logic)
    scoring_result = ScoringService.calculate_rigor_index(mock_study)

    # OUTPUT
    print("\n" + "="*50)
    print(f"VERDICT: {scoring_result.quality_tier.upper()}")
    print(f"SCORE: {scoring_result.score}/14 ({scoring_result.confidence}%)")
    print("="*50)
    print(f"Title: {mock_study.title}")
    print(f"Journal: {mock_study.journal} (IF: {mock_study.impact_factor})")
    print(f"Type: {mock_study.type.upper()}")
    print("-"*50)
    print(f"Breakdown: {scoring_result.score_breakdown.model_dump()}")
    print("="*50 + "\n")


def run() -> None:
    asyncio.run(async_main())

if __name__ == "__main__":
    run()
