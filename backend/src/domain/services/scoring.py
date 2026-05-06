from pydantic import BaseModel, ConfigDict

from ..models.study import QualityTier, ScoreBreakdown, Study

MAX_RIGOR_SCORE = 14


class ScoringResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: int
    confidence: int
    quality_tier: QualityTier
    score_breakdown: ScoreBreakdown


class ScoringService:
    @staticmethod
    def calculate_rigor_index(study: Study) -> ScoringResult:
        """
        Calculates the Rigor Index (0-14 pts) and Confidence.

        The breakdown may include penalties, but the published score is bounded
        to the documented 0-14 scale used by the CLI and downstream adapters.
        Scoring basis reference: docs/scoring_basis.md.
        """
        breakdown = ScoreBreakdown()
        is_rct = study.type.startswith("rct")
        is_double_blind = study.is_double_blind or study.type == "rct_double_blind"
        is_placebo_controlled = study.is_placebo_controlled

        # 1. Study Type (Tier 1)
        if study.type == "meta-analysis":
            breakdown.study_type_pts = 5
        elif is_double_blind and is_placebo_controlled:
            breakdown.study_type_pts = 4
        elif is_double_blind or study.type == "rct_crossover":
            breakdown.study_type_pts = 3
        elif is_rct:
            breakdown.study_type_pts = 2
        elif study.type == "cohort_prospective" and (study.sample_size or 0) > 100:
            breakdown.study_type_pts = 2
        elif study.type == "review_narrative":
            breakdown.study_type_pts = 1

        # 2. Population
        if study.is_human_study:
            if study.population.training_status == "trained":
                breakdown.population_pts = 2
            else:
                breakdown.population_pts = 1
        else:
            breakdown.population_pts = -5

        # 3. Sample Size
        sample_size = study.sample_size or 0
        if sample_size >= 200:
            breakdown.sample_size_pts = 2
        elif 50 <= sample_size < 200:
            breakdown.sample_size_pts = 1
        elif 0 < sample_size < 10:
            breakdown.sample_size_pts = -3

        # 4. Recency
        if study.year >= 2024:
            breakdown.recency_pts = 2
        elif study.year >= 2022:
            breakdown.recency_pts = 1
        elif study.year < 2019:
            breakdown.recency_pts = -1

        # 5. Impact Factor
        if study.impact_factor >= 10:
            breakdown.impact_factor_pts = 2
        elif study.impact_factor >= 5:
            breakdown.impact_factor_pts = 1
        elif study.impact_factor < 2:
            breakdown.impact_factor_pts = -1

        # 6. Methodology and Bias
        if is_placebo_controlled:
            breakdown.methodology_pts += 1
        if is_double_blind:
            breakdown.methodology_pts += 1
        if study.is_preregistered:
            breakdown.methodology_pts += 1

        if study.flags.is_industry_funded:
            breakdown.bias_pts -= 1
        if not study.flags.has_full_text:
            breakdown.bias_pts -= 1

        raw_pts = (
            breakdown.study_type_pts
            + breakdown.population_pts
            + breakdown.sample_size_pts
            + breakdown.recency_pts
            + breakdown.impact_factor_pts
            + breakdown.methodology_pts
            + breakdown.bias_pts
        )

        score = min(MAX_RIGOR_SCORE, max(0, raw_pts))

        # Thresholds: >=8 high | 5-7 moderate | <5 rejected
        if score >= 8:
            quality_tier: QualityTier = "high"
        elif score >= 5:
            quality_tier = "moderate"
        else:
            quality_tier = "rejected"

        # Confidence calculation:
        # base = (score / 14) * 100
        # multiplier: meta-analysis=1.0, double-blind placebo RCT=0.85,
        # RCT=0.75, other=0.5
        # bonus: I2<25% +10 | I2>75% -15 | citations>50 +8 | citations>10 +4
        base_score = (score / MAX_RIGOR_SCORE) * 100

        multiplier = 0.5
        if study.type == "meta-analysis":
            multiplier = 1.0
        elif is_double_blind and is_placebo_controlled:
            multiplier = 0.85
        elif is_rct:
            multiplier = 0.75

        bonuses = 0
        if study.i_squared is not None:
            if study.i_squared < 25:
                bonuses += 10
            elif study.i_squared > 75:
                bonuses -= 15

        citations = study.citation_count or 0
        if citations > 50:
            bonuses += 8
        elif citations > 10:
            bonuses += 4

        confidence = int(min(100, max(0, base_score * multiplier + bonuses)))

        return ScoringResult(
            score=score,
            confidence=confidence,
            quality_tier=quality_tier,
            score_breakdown=breakdown,
        )
