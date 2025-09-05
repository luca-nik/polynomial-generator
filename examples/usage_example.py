#!/usr/bin/env python3
"""
Example usage of the polynomial generator.

This script demonstrates how to use the polynomial generator both 
programmatically and shows the different outputs available.
"""

import numpy as np
from polynomial_generator import generate_random_instance, choose_m_n


def basic_usage_example():
    """Basic example of generating a polynomial."""
    print("=" * 60)
    print("BASIC USAGE EXAMPLE")
    print("=" * 60)
    
    # Generate a polynomial with difficulty δ = 15
    delta = 15
    result = generate_random_instance(delta=delta, seed=42)
    
    print(f"Target difficulty δ: {delta}")
    print(f"Generated polynomial with {result['m']} monomials and {result['n']} variables")
    print(f"Actual baseline: {result['baseline']}")
    print(f"\nPolynomial: {result['polynomial']}")
    print(f"\nExponent matrix K:")
    print(result['matrix'])
    print(f"\nCoefficients: {result['coefficients']}")


def reproducibility_example():
    """Demonstrate reproducibility with seeds."""
    print("\n" + "=" * 60)
    print("REPRODUCIBILITY EXAMPLE")
    print("=" * 60)
    
    seed = 123
    delta = 10
    
    # Generate twice with same seed
    result1 = generate_random_instance(delta=delta, seed=seed)
    result2 = generate_random_instance(delta=delta, seed=seed)
    
    print(f"Using seed {seed} for δ = {delta}")
    print(f"Run 1: m={result1['m']}, n={result1['n']}")
    print(f"Run 2: m={result2['m']}, n={result2['n']}")
    print(f"Results identical: {result1['polynomial'] == result2['polynomial']}")


def different_difficulties_example():
    """Show how polynomials change with different difficulties."""
    print("\n" + "=" * 60)  
    print("DIFFERENT DIFFICULTIES EXAMPLE")
    print("=" * 60)
    
    difficulties = [5, 15, 30, 50]
    
    for delta in difficulties:
        result = generate_random_instance(delta=delta, seed=777)
        print(f"\nδ = {delta:2d}: m={result['m']:2d}, n={result['n']:2d}, "
              f"baseline={result['baseline']:2d}, polynomial degree={_max_total_degree(result['matrix'])}")
        print(f"   Polynomial: {str(result['polynomial'])[:80]}...")


def coefficient_range_example():
    """Demonstrate custom coefficient ranges."""
    print("\n" + "=" * 60)
    print("COEFFICIENT RANGE EXAMPLE")  
    print("=" * 60)
    
    delta = 12
    
    # Different coefficient ranges
    ranges = [(-10, 10), (-2, 2), (1, 5), (-100, -1)]
    
    for coeff_range in ranges:
        result = generate_random_instance(delta=delta, coeff_range=coeff_range, seed=999)
        print(f"Range {coeff_range}: coefficients = {result['coefficients']}")


def chooser_analysis():
    """Analyze the chooser module behavior."""
    print("\n" + "=" * 60)
    print("CHOOSER ANALYSIS")
    print("=" * 60)
    
    delta = 25
    print(f"Analyzing (m, n) choices for δ = {delta} over 20 runs:")
    
    choices = []
    for i in range(20):
        m, n = choose_m_n(delta, seed=i)
        choices.append((m, n))
    
    print(f"Unique (m, n) combinations: {len(set(choices))}")
    print(f"Range of m values: {min(c[0] for c in choices)} to {max(c[0] for c in choices)}")  
    print(f"Range of n values: {min(c[1] for c in choices)} to {max(c[1] for c in choices)}")
    print(f"Most common combinations:")
    
    from collections import Counter
    counter = Counter(choices)
    for (m, n), count in counter.most_common(5):
        print(f"  (m={m}, n={n}): {count} times")


def matrix_analysis_example():
    """Analyze the structure of generated exponent matrices."""
    print("\n" + "=" * 60)
    print("MATRIX ANALYSIS EXAMPLE")
    print("=" * 60)
    
    result = generate_random_instance(delta=20, seed=456)
    matrix = result['matrix']
    
    print(f"Matrix shape: {matrix.shape}")
    print(f"Matrix:\n{matrix}")
    
    # Analyze row properties
    row_degrees = np.sum(matrix, axis=1)
    row_contributions = [max(0, degree - 1) for degree in row_degrees]
    
    print(f"\nRow analysis:")
    for i, (degree, contrib) in enumerate(zip(row_degrees, row_contributions)):
        print(f"  Row {i}: degree = {degree}, contributes {contrib} constraints")
    
    print(f"Total baseline: {sum(row_contributions)} = {result['baseline']}")
    
    # Analyze sparsity
    total_entries = matrix.size
    zero_entries = np.sum(matrix == 0)
    sparsity = zero_entries / total_entries if total_entries > 0 else 0
    
    print(f"\nMatrix sparsity: {sparsity:.2%} zeros")
    print(f"Max exponent: {np.max(matrix)}")
    print(f"Variables used in each monomial: {[np.sum(matrix[i] > 0) for i in range(matrix.shape[0])]}")


def _max_total_degree(matrix: np.ndarray) -> int:
    """Helper: compute maximum total degree of any monomial."""
    if matrix.size == 0:
        return 0
    return int(np.max(np.sum(matrix, axis=1)))


if __name__ == "__main__":
    """Run all examples."""
    basic_usage_example()
    reproducibility_example()
    different_difficulties_example()
    coefficient_range_example()
    chooser_analysis()
    matrix_analysis_example()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)