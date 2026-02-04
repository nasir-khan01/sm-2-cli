"""
SM-2 Spaced Repetition Algorithm Engine

Implements the SuperMemo 2 (SM-2) algorithm for calculating optimal review intervals.
"""

from datetime import date, timedelta
from dataclasses import dataclass


@dataclass
class SRSResult:
    """Result of SM-2 calculation."""
    next_review: date
    interval: int
    ease_factor: float
    repetition: int


def calculate_sm2(
    quality: int,
    repetition: int = 0,
    ease_factor: float = 2.5,
    interval: int = 0
) -> SRSResult:
    """
    Calculate the next review date using the SM-2 algorithm.
    
    Args:
        quality: Quality of response (0-5 scale)
            - 5: Perfect response, easy recall
            - 4: Correct response after hesitation
            - 3: Correct response with serious difficulty
            - 2: Incorrect, but correct answer seemed easy
            - 1: Incorrect, correct answer remembered after showing
            - 0: Complete blackout
        repetition: Number of consecutive successful repetitions
        ease_factor: Current ease factor (minimum 1.3)
        interval: Current interval in days
    
    Returns:
        SRSResult with next_review date, new interval, ease_factor, and repetition
    """
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5")
    
    # Calculate new ease factor
    # EF' = EF + (0.1 - (5 - Q) * (0.08 + (5 - Q) * 0.02))
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # Minimum ease factor is 1.3
    
    if quality < 3:
        # Failed review - reset and review tomorrow
        new_interval = 1
        new_rep = 0
    else:
        # Successful review
        new_rep = repetition + 1
        
        if new_rep == 1:
            new_interval = 1
        elif new_rep == 2:
            new_interval = 6
        else:
            new_interval = round(interval * new_ef)
    
    next_review = date.today() + timedelta(days=new_interval)
    
    return SRSResult(
        next_review=next_review,
        interval=new_interval,
        ease_factor=round(new_ef, 2),
        repetition=new_rep
    )


def quality_from_difficulty(difficulty: str) -> int:
    """
    Map difficulty descriptions to quality scores.
    
    Args:
        difficulty: One of 'again', 'hard', 'good', 'easy'
    
    Returns:
        Quality score (0-5)
    """
    mapping = {
        'again': 1,    # Forgot completely
        'hard': 3,     # Recalled with serious difficulty
        'good': 4,     # Recalled after hesitation  
        'easy': 5,     # Perfect recall
    }
    return mapping.get(difficulty.lower(), 3)
