from ..models.study import Study, ScoreBreakdown, QualityTier

class ScoringService:
    @staticmethod
    def calculate_rigor_index(study: Study) -> Study:
        """
        Calculates the Rigor Index (0-20 pts) based on the FitSci evaluation model.
        Updates the study object with the score and quality tier.
        """
        breakdown = ScoreBreakdown()
        
        # 1. Evidence Level (Max +6)
        if study.type == 'meta-analysis':
            breakdown.study_type_pts = 6
        elif study.type.startswith('rct'):
            breakdown.study_type_pts = 4
        elif study.type in ['cohort_prospective', 'rct_crossover']:
            breakdown.study_type_pts = 3
        elif study.type == 'review_narrative':
            breakdown.study_type_pts = 1
            
        # 2. Measurement Tool (Max +4)
        # Assuming the evaluator extracts keywords like 'MRI', 'USG', 'DEXA'
        keywords_lower = [k.lower() for k in study.keywords]
        if 'mri' in keywords_lower:
            breakdown.methodology_pts += 4
        elif 'ultrasound' in keywords_lower or 'usg' in keywords_lower:
            breakdown.methodology_pts += 2
        elif 'dexa' in keywords_lower:
            breakdown.methodology_pts -= 1
            
        # 3. Subject Status (Max +3)
        if study.population.training_status == 'trained':
            breakdown.population_pts = 3
        elif study.population.training_status in ['untrained', 'sedentary']:
            breakdown.population_pts = 1
            
        # 4. Sample Size (Max +2)
        if study.sample_size and study.sample_size >= 200:
            breakdown.sample_size_pts = 2
        elif study.sample_size and 50 <= study.sample_size < 200:
            breakdown.sample_size_pts = 1
            
        # 5. Recency (Max +2)
        if study.year >= 2024:
            breakdown.recency_pts = 2
        elif study.year >= 2022:
            breakdown.recency_pts = 1
            
        # 6. Impact Factor (Max +2)
        if study.impact_factor >= 10:
            breakdown.impact_factor_pts = 2
        elif study.impact_factor >= 5:
            breakdown.impact_factor_pts = 1
            
        # Total Score
        total_score = (
            breakdown.study_type_pts + 
            breakdown.methodology_pts + 
            breakdown.population_pts + 
            breakdown.sample_size_pts + 
            breakdown.recency_pts + 
            breakdown.impact_factor_pts
        )
        
        # Clamp score between 0 and 20 (though it can be negative with DEXA/Small N)
        study.score = max(0, total_score)
        study.score_breakdown = breakdown
        
        # Assign Quality Tier
        if study.score >= 12:
            study.quality_tier = 'high'
        elif study.score >= 7:
            study.quality_tier = 'moderate'
        else:
            study.quality_tier = 'rejected'
            
        # Calculate Confidence % (Normalized to 100)
        # Note: This is a simplified confidence calculation
        study.confidence = int((study.score / 20) * 100)
        
        return study
