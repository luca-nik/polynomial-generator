"""
Main random instance generation implementing Section 2.4 of the paper.

Generates random polynomial functions with specified baseline difficulty δ.
"""

import random
import numpy as np
import sympy as sp
from typing import Dict, List, Tuple, Optional
from .chooser import choose_m_n


def generate_random_instance(
    delta: int, 
    coeff_range: Tuple[int, int] = (-10, 10),
    seed: Optional[int] = None
) -> Dict:
    """
    Generate random polynomial instance with baseline difficulty δ.
    
    Implementation of Section 2.4 algorithm:
    1. Choose sizes (m, n) using chooser module
    2. Set row totals: sample (E₁, ..., Eₘ) with ∑Eᵢ = δ + m and Eᵢ ≥ 1
    3. Form monomials: distribute each Eᵢ across n variables
    4. Generate random coefficients and build symbolic polynomial
    
    Args:
        delta: Target difficulty parameter (baseline constraint count)
        coeff_range: Range for random coefficients (min, max), excludes 0
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing:
        - delta: input δ
        - m: number of monomials
        - n: number of variables  
        - matrix: exponent matrix K (m×n numpy array)
        - coefficients: list of nonzero coefficients cᵢ
        - polynomial: symbolic SymPy expression
        - baseline: computed baseline Kbase(P) (should equal δ)
    
    Raises:
        ValueError: If delta <= 0 or coefficient range contains only 0
    """
    if delta <= 0:
        raise ValueError(f"Delta must be positive, got {delta}")
    
    if coeff_range[0] >= 0 and coeff_range[1] <= 0:
        raise ValueError(f"Coefficient range {coeff_range} must allow nonzero values")
    
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Step 1: Choose sizes
    m, n = choose_m_n(delta, seed)
    
    # Step 2: Set row totals - sample (E₁,...,Eₘ) with ∑Eᵢ = δ + m, Eᵢ ≥ 1
    row_totals = _sample_row_totals(m, delta + m)
    
    # Step 3: Form monomials - distribute each Eᵢ across n variables
    exponent_matrix = np.zeros((m, n), dtype=int)
    for i, total_degree in enumerate(row_totals):
        exponent_matrix[i] = _distribute_exponents(total_degree, n)
    
    # Step 4: Generate random nonzero coefficients
    coefficients = []
    for _ in range(m):
        coeff = 0
        while coeff == 0:  # Ensure nonzero coefficients
            coeff = random.randint(coeff_range[0], coeff_range[1])
        coefficients.append(coeff)
    
    # Step 5: Create symbolic polynomial using SymPy
    x = sp.symbols([f'x{i+1}' for i in range(n)])
    polynomial = sum(
        coeff * sp.prod([x[j]**exponent_matrix[i,j] for j in range(n)])
        for i, coeff in enumerate(coefficients)
    )
    
    # Verify baseline calculation
    baseline = _calculate_baseline(exponent_matrix)
    
    return {
        'delta': delta,
        'm': m, 
        'n': n,
        'matrix': exponent_matrix,
        'coefficients': coefficients,
        'polynomial': polynomial,
        'baseline': baseline
    }


def _sample_row_totals(m: int, target_sum: int) -> List[int]:
    """
    Sample m positive integers (E₁, ..., Eₘ) that sum to target_sum.
    
    Each Eᵢ ≥ 1 represents the total degree of monomial i.
    
    Args:
        m: Number of monomials
        target_sum: Required sum ∑Eᵢ = δ + m
        
    Returns:
        List of m positive integers summing to target_sum
        
    Raises:
        ValueError: If target_sum < m (impossible to have all Eᵢ ≥ 1)
    """
    if target_sum < m:
        raise ValueError(f"Cannot distribute {target_sum} across {m} monomials with Eᵢ ≥ 1")
    
    # Reserve 1 for each monomial, then distribute remaining sum
    remaining = target_sum - m
    
    if remaining == 0:
        # All monomials have degree exactly 1
        return [1] * m
    
    # Use Dirichlet distribution (via gamma) for more natural distribution
    # than purely uniform multinomial
    alphas = np.ones(m)  # Symmetric Dirichlet
    proportions = np.random.dirichlet(alphas)
    
    # Convert proportions to integer distribution
    extras = np.round(proportions * remaining).astype(int)
    
    # Adjust to ensure exact sum (handle rounding errors)
    diff = remaining - sum(extras)
    if diff != 0:
        # Randomly adjust some entries to fix the sum
        indices = np.random.choice(m, abs(diff), replace=True)
        for idx in indices:
            extras[idx] += 1 if diff > 0 else -1
    
    # Final result: base 1 + extras
    return [1 + extra for extra in extras]


def _distribute_exponents(total_degree: int, n_variables: int) -> np.ndarray:
    """
    Distribute total_degree across n_variables to form exponent vector.
    
    Creates exponent vector (k₁, ..., kₙ) where ∑kⱼ = total_degree.
    Distributes more equally across variables rather than creating sparse vectors.
    
    Args:
        total_degree: Total degree to distribute (Eᵢ)
        n_variables: Number of variables
        
    Returns:
        numpy array of length n_variables with exponents summing to total_degree
    """
    if total_degree == 0:
        return np.zeros(n_variables, dtype=int)
    
    # Use symmetric Dirichlet distribution with higher alpha for more equal distribution
    alphas = np.ones(n_variables) * 2.0  # Higher alpha = more equal distribution
    proportions = np.random.dirichlet(alphas)
    
    # Convert to integer distribution
    exponents = np.round(proportions * total_degree).astype(int)
    
    # Adjust to ensure exact sum
    diff = total_degree - sum(exponents)
    if diff != 0:
        # Randomly adjust entries to fix sum
        indices = np.random.choice(n_variables, abs(diff), replace=True)
        for idx in indices:
            if diff > 0:
                exponents[idx] += 1
            elif exponents[idx] > 0:  # Can only subtract if positive
                exponents[idx] -= 1
            else:
                # Find a positive entry to subtract from
                pos_indices = np.where(exponents > 0)[0]
                if len(pos_indices) > 0:
                    exponents[np.random.choice(pos_indices)] -= 1
    
    return exponents


def _calculate_baseline(exponent_matrix: np.ndarray) -> int:
    """
    Calculate baseline constraint count Kbase(P) from exponent matrix.
    
    Kbase(P) = ∑ᵢ max(0, Eᵢ - 1) where Eᵢ = ∑ⱼ kⱼ,ᵢ
    
    Args:
        exponent_matrix: m×n matrix where entry (i,j) is exponent of variable j in monomial i
        
    Returns:
        Baseline constraint count (should equal input δ)
    """
    row_degrees = np.sum(exponent_matrix, axis=1)  # Eᵢ for each monomial
    return sum(max(0, degree - 1) for degree in row_degrees)