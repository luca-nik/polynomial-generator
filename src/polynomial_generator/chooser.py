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
        - m = number of monomials (≈ δ * α)
        - n = number of variables (≈ sqrt(δ) / β)

    Notes:
        - α, β ∈ [0.2, 0.8] chosen uniformly at random
        - n is sublinear in δ, avoiding explosion
        - m is linear in δ, controlling average monomial degree
    """
    if delta <= 0:
        raise ValueError(f"Delta must be positive, got {delta}")

    if seed is not None:
        random.seed(seed)

    alpha = random.uniform(0.6, 1.5)
    beta = random.uniform(0.2, 0.8)

    m = max(1, int(math.sqrt(delta) * alpha))
    n = max(2, int(math.sqrt(delta) / beta))

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