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
        primary_outcome="CSA"
    )
    
    scored_study = ScoringService.calculate_rigor_index(study)
    
    # Expected: 6 (Meta) + 4 (MRI) + 3 (Trained) + 2 (N>200) + 2 (2024) + 2 (IF>10) = 19
    assert scored_study.score == 19
    assert scored_study.quality_tier == "high"
    assert scored_study.confidence == 95

def test_rigor_index_rct_low_quality():
    study = Study(
        id="PMC67890",
        pmc_url="https://example.com",
        title="Small RCT",
        authors=["Author B"],
        journal="Low IF Journal",
        year=2020,
        impact_factor=1.5,
        type="rct",
        topic="hypertrophy",
        subtopic="supplements",
        keywords=["DEXA", "Untrained"],
        sample_size=20,
        population=Population(training_status="untrained"),
        primary_outcome="LBM"
    )
    
    scored_study = ScoringService.calculate_rigor_index(study)
    
    # Expected: 4 (RCT) - 1 (DEXA) + 1 (Untrained) + 0 (N<50) + 0 (2020) + 0 (IF<5) = 4
    assert scored_study.score == 4
    assert scored_study.quality_tier == "rejected"
    assert scored_study.confidence == 20
