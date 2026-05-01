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
    
    # Expected Points:
    # 0 (rct - but not double blind/placebo specified in points but study type starts with rct)
    # wait, if type='rct' but is_double_blind=False and is_placebo_controlled=False, it gets 0 pts for study type in my implementation
    # 0 (type) - 5 (animal) + 0 (N<50) + 1 (2023) - 1 (IF<2) = -5
    assert scored_study.score == -5
    assert scored_study.quality_tier == "rejected"
    assert scored_study.confidence == 0

def test_rigor_index_rct_moderate():
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
