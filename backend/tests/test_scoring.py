import pytest
from src.domain.models.study import Study, Population
from src.domain.services.scoring import ScoringService

def test_rigor_index_meta_analysis_high_quality():
    study = Study(
        id="PMC12345",
        pmc_url="https://example.com",
        title="Meta-analysis of Hypertrophy",
        authors=["Author A"],
        journal="Journal of Strength",
        year=2024,
        impact_factor=12.0,
        type="meta-analysis",
        topic="hypertrophy",
        subtopic="volume",
        keywords=["MRI", "Trained"],
        sample_size=300,
        population=Population(training_status="trained"),
        primary_outcome="CSA",
        citation_count=60,
        i_squared=15
    )
    
    scored_study = ScoringService.calculate_rigor_index(study)
    
    # Expected Points:
    # 5 (Meta) + 2 (Trained) + 2 (N>200) + 2 (2024) + 2 (IF>10) = 13 raw
    assert scored_study.score == 13
    assert scored_study.quality_tier == "high"
    
    # Confidence calculation:
    # base = (13/14) * 100 = 92.85
    # multiplier = 1.0 (meta)
    # bonuses = 10 (I2<25) + 8 (cit>50) = 18
    # conf = min(100, 92.85 * 1.0 + 18) = 100
    assert scored_study.confidence == 100

def test_rigor_index_animal_study_reject():
    study = Study(
        id="PMC001",
        pmc_url="https://example.com",
        title="Mice on Creatine",
        authors=["Scientist"],
        journal="Animal Biol",
        year=2023,
        impact_factor=1.0,
        type="rct",
        topic="creatine",
        subtopic="dosage",
        is_human_study=False,
        sample_size=20,
        primary_outcome="Growth"
    )
    
    scored_study = ScoringService.calculate_rigor_index(study)
    
    # Raw breakdown is negative after penalties, but the published score stays
    # on the documented 0-14 scale.
    assert scored_study.score == 0
    assert scored_study.quality_tier == "rejected"
    assert scored_study.confidence == 0

def test_rigor_index_rct_high_quality():
    study = Study(
        id="PMC999",
        pmc_url="https://example.com",
        title="Human RCT",
        authors=["Author C"],
        journal="Nutrients",
        year=2022,
        impact_factor=5.9,
        type="rct",
        is_double_blind=True,
        is_placebo_controlled=True,
        topic="protein",
        subtopic="timing",
        sample_size=60,
        population=Population(training_status="untrained"),
        primary_outcome="MPS"
    )
    
    scored_study = ScoringService.calculate_rigor_index(study)
    
    # Expected Points:
    # 4 (RCT DB+Placebo) + 1 (Untrained) + 1 (N 50-200) + 1 (2022) + 1 (IF 5-10) + 2 (Methodology: DB+Placebo) = 10 raw
    # Wait, my implementation for RCT DB+Placebo adds 4 to study_type_pts AND then methodology adds +1 for DB and +1 for Placebo?
    # GEMINI.md says: 
    # Meta-analiza / Systematic Review +5
    # RCT double-blind placebo +4
    # RCT single-blind / crossover +3
    # ...
    # Placebo-controlled +1
    # Double-blind +1
    # So yes, they are additive in the matrix.
    assert scored_study.score == 10
    assert scored_study.quality_tier == "high" # 10 >= 8 is high

def test_rigor_index_uses_rct_double_blind_type_without_duplicate_boolean():
    study = Study(
        id="PMC777",
        pmc_url="https://example.com",
        title="Double blind RCT from structured type",
        authors=["Author D"],
        journal="Applied Physiology",
        year=2024,
        impact_factor=6.0,
        type="rct_double_blind",
        topic="supplements",
        subtopic="ergogenic",
        sample_size=80,
        population=Population(training_status="trained"),
        primary_outcome="Power output"
    )

    scored_study = ScoringService.calculate_rigor_index(study)

    assert scored_study.score_breakdown.study_type_pts == 3
    assert scored_study.score_breakdown.methodology_pts == 1
    assert scored_study.score == 10
    assert scored_study.quality_tier == "high"

def test_rigor_index_is_bounded_to_documented_scale():
    study = Study(
        id="PMC888",
        pmc_url="https://example.com",
        title="Maximal scoring RCT",
        authors=["Author E"],
        journal="Elite Journal",
        year=2024,
        impact_factor=20.0,
        type="rct_double_blind",
        is_placebo_controlled=True,
        is_preregistered=True,
        topic="protein",
        subtopic="dose response",
        sample_size=250,
        population=Population(training_status="trained"),
        primary_outcome="Lean mass"
    )

    scored_study = ScoringService.calculate_rigor_index(study)

    assert scored_study.score == 14
    assert scored_study.confidence <= 100
