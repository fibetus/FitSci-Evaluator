import asyncio
import argparse
from ..domain.models.study import Study, Population
from ..domain.services.scoring import ScoringService

async def async_main():
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
        summary_en="High volume training leads to superior hypertrophy outcomes in trained individuals."
    )

    # THE JUDGE (Pure logic)
    evaluated_study = ScoringService.calculate_rigor_index(mock_study)

    # OUTPUT
    print("\n" + "="*50)
    print(f"VERDICT: {evaluated_study.quality_tier.upper()}")
    print(f"SCORE: {evaluated_study.score}/14 ({evaluated_study.confidence}%)")
    print("="*50)
    print(f"Title: {evaluated_study.title}")
    print(f"Journal: {evaluated_study.journal} (IF: {evaluated_study.impact_factor})")
    print(f"Type: {evaluated_study.type.upper()}")
    print("-"*50)
    print(f"Breakdown: {evaluated_study.score_breakdown.model_dump()}")
    print("="*50 + "\n")

def run():
    asyncio.run(async_main())

if __name__ == "__main__":
    run()
