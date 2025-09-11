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
    coeff_range: Tuple[float, float] = (-10, 10),
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
    
    # Enforce matrix properties:
    # - No identical rows
    # - No columns with all zeros
    exponent_matrix = _enforce_matrix_constraints(exponent_matrix)
    
    # Step 4: Generate random nonzero coefficients
    coefficients = []
    for _ in range(m):
        coeff = 0
        while coeff == 0:  # Ensure nonzero coefficients
            coeff = random.uniform(coeff_range[0], coeff_range[1])
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


def _enforce_matrix_constraints(exponent_matrix: np.ndarray) -> np.ndarray:
    """
    Post-process the exponent matrix to ensure:
    - No duplicate rows
    - No columns are entirely zero

    The adjustments preserve each row's total degree, so the baseline δ remains
    unchanged. The procedure preferentially adds mass to under-covered columns
    when breaking duplicates and when fixing zero-columns.

    Args:
        exponent_matrix: m×n nonnegative integer matrix

    Returns:
        Adjusted matrix meeting the constraints.
    """
    if exponent_matrix.size == 0:
        return exponent_matrix

    m, n = exponent_matrix.shape
    matrix = exponent_matrix.copy()

    # Helper to move one unit from column p -> q in a given row (in-place on row)
    def _move_unit(row: np.ndarray, p: int, q: int) -> None:
        if p == q:
            return
        if row[p] <= 0:
            return
        row[p] -= 1
        row[q] += 1

    # Track counts of row patterns to check uniqueness efficiently
    from collections import Counter
    seen = Counter(tuple(row.tolist()) for row in matrix)

    # Break duplicate rows by shifting one unit towards least-covered columns
    col_sums = matrix.sum(axis=0).astype(int)
    for i in range(m):
        row = matrix[i]
        key = tuple(row.tolist())
        if seen[key] <= 1:
            continue  # already unique

        # Try multiple perturbations to reach a unique row, favor columns with low coverage
        attempts = 0
        made_unique = False
        while attempts < 100 and not made_unique:
            # Choose a target column to increase: zero columns first, else least-covered
            zero_cols = np.where(col_sums == 0)[0]
            if len(zero_cols) > 0:
                q = int(zero_cols[attempts % len(zero_cols)])
            else:
                q = int(np.argmin(col_sums))

            # Choose a donor column with positive mass, not equal to q
            donors = [p for p in np.where(row > 0)[0].tolist() if p != q]
            if not donors:
                break
            p = donors[0]

            # Propose move
            cand = row.copy()
            _move_unit(cand, p, q)
            cand_key = tuple(cand.tolist())
            if seen[cand_key] == 0:
                # Apply move and update bookkeeping
                matrix[i] = cand
                seen[key] -= 1
                if seen[key] == 0:
                    del seen[key]
                seen[cand_key] += 1
                col_sums[p] -= 1
                col_sums[q] += 1
                key = cand_key
                row = cand
                made_unique = True
                break

            attempts += 1

        if not made_unique:
            # Exhaustive deterministic search over single-unit moves
            found = False
            for p in range(n):
                if row[p] == 0:
                    continue
                for q in range(n):
                    if q == p:
                        continue
                    cand = row.copy()
                    _move_unit(cand, p, q)
                    cand_key = tuple(cand.tolist())
                    if seen[cand_key] == 0:
                        matrix[i] = cand
                        seen[key] -= 1
                        if seen[key] == 0:
                            del seen[key]
                        seen[cand_key] += 1
                        col_sums[p] -= 1
                        col_sums[q] += 1
                        key = cand_key
                        row = cand
                        found = True
                        break
                if found:
                    break
            # If still not found, leave as-is (uniqueness may be impossible in edge cases)

    # Ensure no column is entirely zero by redistributing within rows
    col_sums = matrix.sum(axis=0).astype(int)
    zero_columns = np.where(col_sums == 0)[0].tolist()
    if zero_columns:
        # Recompute seen to reflect current matrix
        seen = Counter(tuple(row.tolist()) for row in matrix)

    for j in zero_columns:
        fixed = False
        # Try to shift from rows with available mass, avoiding duplicates
        for i in range(m):
            row = matrix[i]
            donors = [p for p in np.where(row > 0)[0].tolist() if p != j]
            # Try donors in descending amount to reduce risk of zeroing
            donors.sort(key=lambda p: row[p], reverse=True)
            for p in donors:
                cand = row.copy()
                cand[p] -= 1
                cand[j] += 1
                old_key = tuple(row.tolist())
                new_key = tuple(cand.tolist())
                if seen[new_key] == 0:
                    matrix[i] = cand
                    seen[old_key] -= 1
                    if seen[old_key] == 0:
                        del seen[old_key]
                    seen[new_key] += 1
                    col_sums[p] -= 1
                    col_sums[j] += 1
                    fixed = True
                    break
            if fixed:
                break
        # If we couldn't avoid duplicates, perform the move anyway then try to re-break duplicates
        if not fixed:
            for i in range(m):
                row = matrix[i]
                donors = [p for p in np.where(row > 0)[0].tolist() if p != j]
                if not donors:
                    continue
                p = donors[0]
                old_key = tuple(row.tolist())
                row[p] -= 1
                row[j] += 1
                new_key = tuple(row.tolist())
                seen[old_key] -= 1
                if seen[old_key] == 0:
                    del seen[old_key]
                seen[new_key] += 1
                col_sums[p] -= 1
                col_sums[j] += 1
                matrix[i] = row
                # Attempt to break any duplicate created for this row with a secondary move
                if seen[new_key] > 1:
                    # Move from the largest donor to the least-covered non-j column
                    donors2 = [p2 for p2 in np.where(row > 0)[0].tolist() if p2 != j]
                    if donors2:
                        q2_candidates = [q for q in range(n) if q != j]
                        # pick least covered among candidates
                        q2 = min(q2_candidates, key=lambda q: col_sums[q]) if q2_candidates else None
                        if q2 is not None and donors2:
                            p2 = donors2[0]
                            cand2 = row.copy()
                            _move_unit(cand2, p2, q2)
                            k2 = tuple(cand2.tolist())
                            if seen[k2] == 0:
                                matrix[i] = cand2
                                seen[new_key] -= 1
                                if seen[new_key] == 0:
                                    del seen[new_key]
                                seen[k2] += 1
                                col_sums[p2] -= 1
                                col_sums[q2] += 1
                break  # proceed to next zero column

    return matrix
