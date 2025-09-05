"""
Logic for choosing number of monomials (m) and variables (n) given difficulty δ.

This module isolates the size selection strategy, making it easily replaceable
with different heuristics without affecting other components.
"""

import random
import math
from typing import Tuple, Optional


def choose_m_n(delta: int, seed: Optional[int] = None) -> Tuple[int, int]:
    """
    Choose number of monomials (m) and variables (n) given difficulty δ.
    
    Args:
        delta: Difficulty parameter (target baseline constraint count)
        seed: Random seed for reproducibility
    
    Returns:
        (m, n) tuple where:
        - m = number of monomials  
        - n = number of variables
    
    Rules:
        - m ∈ [1, min(δ, ⌊√δ⌋ + 5)]
        - n ∈ [2, min(δ, m+3, 10)]
        
    Note:
        Same δ may give different (m, n) due to randomization.
        This function is replaceable for different size selection strategies.
    """
    if delta <= 0:
        raise ValueError(f"Delta must be positive, got {delta}")
    
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
    
    # Choose m: at least 1, at most δ, random in growing range
    max_m = min(delta, int(math.sqrt(delta)) + 5)
    m = random.randint(1, max_m)
    
    # Choose n: at least 2, capped to avoid explosion  
    max_n = min(delta, m + 3, 10)
    max_n = max(max_n, 2)  # Ensure max_n >= 2 so we can choose n >= 2
    n = random.randint(2, max_n)
    
    return m, n


def validate_m_n(m: int, n: int, delta: int) -> bool:
    """
    Validate that chosen (m, n) can support the target delta.
    
    For the polynomial to have baseline exactly δ, we need:
    - Each monomial i has degree Eᵢ ≥ 1
    - Sum of degrees ∑Eᵢ = δ + m
    - This must be feasible given n variables
    
    Args:
        m: Number of monomials
        n: Number of variables
        delta: Target difficulty
        
    Returns:
        True if (m, n, delta) combination is feasible
    """
    if m <= 0 or n <= 1 or delta < 0:
        return False
        
    # We need to distribute δ + m total degree across m monomials
    # with each monomial having degree ≥ 1
    min_total_degree = m  # Each Eᵢ ≥ 1
    required_total_degree = delta + m
    
    return required_total_degree >= min_total_degree