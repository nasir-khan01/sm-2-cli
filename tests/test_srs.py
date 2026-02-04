"""
Test suite for the SM-2 Spaced Repetition Algorithm.

Tests verify that:
1. Easy scores (5) produce longer intervals than Hard scores (3)
2. Score < 3 resets interval to 1 day (tomorrow)
3. Ease factor never drops below 1.3
4. First successful review has interval = 1, second = 6
5. Subsequent intervals multiply by ease factor
"""

import pytest
from datetime import date, timedelta

from dsaprep.srs import calculate_sm2, SRSResult, quality_from_difficulty


class TestSM2Algorithm:
    """Tests for the core SM-2 algorithm calculations."""
    
    def test_first_review_interval_is_one_day(self):
        """First successful review should have interval of 1 day."""
        result = calculate_sm2(quality=4, repetition=0, ease_factor=2.5, interval=0)
        
        assert result.interval == 1
        assert result.repetition == 1
        assert result.next_review == date.today() + timedelta(days=1)
    
    def test_second_review_interval_is_six_days(self):
        """Second successful review should have interval of 6 days."""
        result = calculate_sm2(quality=4, repetition=1, ease_factor=2.5, interval=1)
        
        assert result.interval == 6
        assert result.repetition == 2
        assert result.next_review == date.today() + timedelta(days=6)
    
    def test_third_review_multiplies_by_ease_factor(self):
        """Third+ review interval = previous_interval * ease_factor."""
        result = calculate_sm2(quality=4, repetition=2, ease_factor=2.5, interval=6)
        
        # 6 * 2.5 = 15
        assert result.interval == 15
        assert result.repetition == 3
    
    def test_easy_score_produces_longer_interval_than_hard(self):
        """Easy score (5) should result in longer intervals than Hard (3)."""
        easy_result = calculate_sm2(quality=5, repetition=2, ease_factor=2.5, interval=6)
        hard_result = calculate_sm2(quality=3, repetition=2, ease_factor=2.5, interval=6)
        
        # Easy score increases ease factor, Hard score decreases it
        # Both multiply interval by (updated) ease factor
        assert easy_result.interval > hard_result.interval
        assert easy_result.ease_factor > hard_result.ease_factor
    
    def test_failed_review_resets_to_tomorrow(self):
        """Score < 3 should reset interval to 1 day (tomorrow)."""
        # Test with score 0 (complete blackout)
        result_0 = calculate_sm2(quality=0, repetition=5, ease_factor=2.5, interval=30)
        assert result_0.interval == 1
        assert result_0.repetition == 0
        assert result_0.next_review == date.today() + timedelta(days=1)
        
        # Test with score 1
        result_1 = calculate_sm2(quality=1, repetition=5, ease_factor=2.5, interval=30)
        assert result_1.interval == 1
        assert result_1.repetition == 0
        
        # Test with score 2
        result_2 = calculate_sm2(quality=2, repetition=5, ease_factor=2.5, interval=30)
        assert result_2.interval == 1
        assert result_2.repetition == 0
    
    def test_ease_factor_minimum_is_1_3(self):
        """Ease factor should never drop below 1.3."""
        # Repeatedly give low scores to drive down ease factor
        result = calculate_sm2(quality=0, repetition=0, ease_factor=1.3, interval=1)
        assert result.ease_factor >= 1.3
        
        # Even with already-low ease factor
        result = calculate_sm2(quality=1, repetition=0, ease_factor=1.5, interval=1)
        assert result.ease_factor >= 1.3
    
    def test_ease_factor_increases_with_high_scores(self):
        """High scores (4-5) should increase ease factor."""
        original_ef = 2.5
        
        result_4 = calculate_sm2(quality=4, repetition=0, ease_factor=original_ef, interval=0)
        # quality=4: ef + (0.1 - (5-4) * (0.08 + (5-4) * 0.02)) = ef + 0.1 - 0.1 = ef
        # So score of 4 maintains ease factor
        
        result_5 = calculate_sm2(quality=5, repetition=0, ease_factor=original_ef, interval=0)
        # quality=5: ef + (0.1 - (5-5) * ...) = ef + 0.1 = 2.6
        assert result_5.ease_factor > original_ef
    
    def test_ease_factor_decreases_with_low_scores(self):
        """Low scores (0-2) should decrease ease factor."""
        original_ef = 2.5
        
        result = calculate_sm2(quality=2, repetition=0, ease_factor=original_ef, interval=0)
        assert result.ease_factor < original_ef
    
    def test_invalid_quality_raises_error(self):
        """Quality outside 0-5 range should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_sm2(quality=-1, repetition=0, ease_factor=2.5, interval=0)
        
        with pytest.raises(ValueError):
            calculate_sm2(quality=6, repetition=0, ease_factor=2.5, interval=0)


class TestQualityMapping:
    """Tests for difficulty-to-quality score mapping."""
    
    def test_again_maps_to_1(self):
        assert quality_from_difficulty('again') == 1
    
    def test_hard_maps_to_3(self):
        assert quality_from_difficulty('hard') == 3
    
    def test_good_maps_to_4(self):
        assert quality_from_difficulty('good') == 4
    
    def test_easy_maps_to_5(self):
        assert quality_from_difficulty('easy') == 5
    
    def test_case_insensitive(self):
        assert quality_from_difficulty('EASY') == 5
        assert quality_from_difficulty('Hard') == 3
    
    def test_unknown_defaults_to_3(self):
        assert quality_from_difficulty('unknown') == 3


class TestSRSResult:
    """Tests for the SRSResult dataclass."""
    
    def test_result_contains_all_fields(self):
        result = calculate_sm2(quality=4, repetition=0, ease_factor=2.5, interval=0)
        
        assert hasattr(result, 'next_review')
        assert hasattr(result, 'interval')
        assert hasattr(result, 'ease_factor')
        assert hasattr(result, 'repetition')
        
        assert isinstance(result.next_review, date)
        assert isinstance(result.interval, int)
        assert isinstance(result.ease_factor, float)
        assert isinstance(result.repetition, int)
