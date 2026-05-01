from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Topic and Type definitions matching the Scientist Scraper spec
StudyTopic = Literal[
    'hypertrophy', 'protein', 'creatine', 'peptides', 
    'supplements', 'hormones', 'periodization', 'recovery', 'injury'
]

StudyType = Literal[
    'meta-analysis', 'rct', 'rct_double_blind', 'rct_crossover', 
    'cohort_prospective', 'review_narrative', 'case_study'
]

QualityTier = Literal['high', 'moderate', 'rejected']
LegalStatus = Literal['legal', 'wada_prohibited', 'research_only', 'unclear']

class Population(BaseModel):
    age_range: Optional[str] = None
    sex: Optional[Literal['male', 'female', 'mixed']] = None
    training_status: Optional[Literal['trained', 'untrained', 'sedentary', 'mixed']] = None
    health_status: Optional[Literal['healthy', 'clinical']] = None

class Delta(BaseModel):
    test_group_change_pct: Optional[float] = None
    placebo_change_pct: Optional[float] = None
    net_effect_pct: Optional[float] = None
    effect_size: Optional[float] = None
    effect_size_type: Optional[Literal['cohens_d', 'hedges_g', 'OR', 'SMD']] = None
    p_value: Optional[float] = None
    is_significant: bool = False

class Dosage(BaseModel):
    amount: Optional[str] = None
    unit: Optional[str] = None
    protocol: Optional[str] = None
    timing: Optional[str] = None

class ScoreBreakdown(BaseModel):
    study_type_pts: int = 0
    population_pts: int = 0
    sample_size_pts: int = 0
    recency_pts: int = 0
    impact_factor_pts: int = 0
    methodology_pts: int = 0

class Study(BaseModel):
    id: str = Field(..., description="PMC ID")
    pmid: Optional[str] = None
    doi: Optional[str] = None
    pmc_url: str
    
    title: str
    authors: List[str]
    journal: str
    year: int
    impact_factor: float
    if_source: Literal['lookup', 'crossref', 'estimated'] = 'estimated'
    citation_count: Optional[int] = None
    is_open_access: bool = False
    is_preprint: bool = False
    funding_source: Optional[str] = None
    
    type: StudyType
    topic: StudyTopic
    subtopic: str
    keywords: List[str] = []
    
    sample_size: Optional[int] = None
    duration_weeks: Optional[int] = None
    population: Population = Field(default_factory=Population)
    
    is_human_study: bool = True
    is_double_blind: bool = False
    is_placebo_controlled: bool = False
    is_preregistered: bool = False
    has_conflict_of_interest: Optional[bool] = None
    
    primary_outcome: str
    delta: Optional[Delta] = None
    dosage: Optional[Dosage] = None
    
    score: int = 0
    confidence: int = 0
    quality_tier: QualityTier = 'moderate'
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    
    summary_pl: Optional[str] = None
    summary_en: Optional[str] = None
    key_findings: List[str] = []
    practical_note: Optional[str] = None
    caveats: List[str] = []
    
    status: LegalStatus = 'unclear'
    flags: dict = Field(default_factory=lambda: {
        "is_industry_funded": False,
        "is_preprint": False,
        "has_full_text": True,
        "needs_manual_review": False
    })
    
    scraped_at: datetime = Field(default_factory=datetime.now)
