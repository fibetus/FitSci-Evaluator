from ..models.study import Study, ScoreBreakdown

class ScoringService:
    @staticmethod
    def calculate_rigor_index(study: Study) -> Study:
        """
        Calculates the Rigor Index (0-14 pts raw, then mapped) and Confidence
        based on the FitSci Scientist Scraper spec in GEMINI.md.
        """
        breakdown = ScoreBreakdown()
        raw_pts = 0

        # 1. Study Type (Tier 1)
        if study.type == 'meta-analysis':
            breakdown.study_type_pts = 5
        elif study.is_double_blind and study.is_placebo_controlled:
            breakdown.study_type_pts = 4
        elif study.is_double_blind or study.type == 'rct_crossover':
            breakdown.study_type_pts = 3
        elif study.type == 'cohort_prospective' and (study.sample_size or 0) > 100:
            breakdown.study_type_pts = 2
        elif study.type == 'review_narrative':
            breakdown.study_type_pts = 1
        
        # 2. Population
        if study.is_human_study:
            if study.population.training_status == 'trained':
                breakdown.population_pts = 2
            else:
                breakdown.population_pts = 1
        else:
            breakdown.population_pts = -5  # Animal / In-vitro

        # 3. Sample Size
        if (study.sample_size or 0) >= 200:
            breakdown.sample_size_pts = 2
        elif 50 <= (study.sample_size or 0) < 200:
            breakdown.sample_size_pts = 1
        elif (study.sample_size or 0) < 10 and (study.sample_size or 0) > 0:
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

        # 6. Methodology & Bias (Combined into bias_pts/methodology_pts)
        if study.is_placebo_controlled:
            breakdown.methodology_pts += 1
        if study.is_double_blind:
            breakdown.methodology_pts += 1
        if study.is_preregistered:
            breakdown.methodology_pts += 1
        
        if study.flags.get("is_industry_funded"):
            breakdown.bias_pts -= 1
        if not study.flags.get("has_full_text"):
            breakdown.bias_pts -= 1

        raw_pts = (
            breakdown.study_type_pts + 
            breakdown.population_pts + 
            breakdown.sample_size_pts + 
            breakdown.recency_pts + 
            breakdown.impact_factor_pts + 
            breakdown.methodology_pts +
            breakdown.bias_pts
        )

        study.score = raw_pts
        study.score_breakdown = breakdown

        # Thresholds: >=8 -> high | 5–7 → moderate | <5 → REJECT
        if study.score >= 8:
            study.quality_tier = 'high'
        elif study.score >= 5:
            study.quality_tier = 'moderate'
        else:
            study.quality_tier = 'rejected'

        # Confidence Calculation
        # base = (raw_pts / 14) * 100
        # multiplier: meta-analysis=1.0, rct_double_blind=0.85, rct=0.75, other=0.5
        # bonus: I²<25% → +10 | I²>75% → -15 | citations>50 → +8 | citations>10 → +4
        
        base_score = (max(0, raw_pts) / 14) * 100
        
        multiplier = 0.5
        if study.type == 'meta-analysis':
            multiplier = 1.0
        elif study.is_double_blind and study.is_placebo_controlled:
            multiplier = 0.85
        elif study.type.startswith('rct'):
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
            
        study.confidence = int(min(100, max(0, base_score * multiplier + bonuses)))

        return study
