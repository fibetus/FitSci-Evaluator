"""LLM extraction output — excludes Judge-owned fields (score, tier, timestamps)."""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from .study import (
    Delta,
    Dosage,
    LegalStatus,
    Population,
    Study,
    StudyFlags,
    StudyTopic,
    StudyType,
)

JUDGE_OWNED_FIELDS = frozenset(
    {"score", "confidence", "quality_tier", "score_breakdown", "scraped_at"}
)


class ExtractionResult(BaseModel):
    """Structured fields produced by the Sifter; scoring is always applied by the Judge."""

    id: str = Field(..., description="PMC ID")
    pmid: Optional[str] = None
    doi: Optional[str] = None
    pmc_url: str

    title: str
    authors: List[str]
    journal: str
    year: int
    impact_factor: float
    if_source: Literal["lookup", "crossref", "estimated"] = "estimated"
    citation_count: Optional[int] = None
    is_open_access: bool = False
    is_preprint: bool = False
    funding_source: Optional[str] = None
    i_squared: Optional[float] = None

    type: StudyType
    topic: StudyTopic
    subtopic: str
    keywords: List[str] = Field(default_factory=list)

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

    summary_pl: Optional[str] = None
    summary_en: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    practical_note: Optional[str] = None
    caveats: List[str] = Field(default_factory=list)

    status: LegalStatus = "unclear"
    flags: StudyFlags = Field(default_factory=StudyFlags)

    def into_study(self, *, study_id: str | None = None) -> Study:
        payload = self.model_dump()
        if study_id is not None:
            payload["id"] = study_id
        return Study.model_validate(payload)

    @classmethod
    def from_llm_json(cls, data: dict[str, Any]) -> "ExtractionResult":
        cleaned = {k: v for k, v in data.items() if k not in JUDGE_OWNED_FIELDS}
        return cls.model_validate(cleaned)
