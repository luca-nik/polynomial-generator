"""
Command-line interface for generating random polynomial instances.

Provides a simple CLI to generate polynomials with specified difficulty parameter.
"""

import click
import numpy as np
from .instance_generator import generate_random_instance


@click.command()
@click.option(
    '--delta', 
    required=True, 
    type=int, 
    help='Difficulty parameter δ (target baseline constraint count)'
)
@click.option(
    '--seed', 
    type=int, 
    help='Random seed for reproducibility'
)
@click.option(
    '--coeff-min',
    type=int,
    default=-10,
    help='Minimum coefficient value (default: -10)'
)
@click.option(
    '--coeff-max',
    type=int,
    default=10,
    help='Maximum coefficient value (default: 10)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed output including algorithm steps'
)
def main(delta: int, seed: int, coeff_min: int, coeff_max: int, verbose: bool):
    """
    Generate random polynomial instance with given difficulty parameter δ.
    
    The algorithm follows Section 2.4 of the paper:
    1. Choose number of monomials (m) and variables (n)
    2. Sample row totals with ∑Eᵢ = δ + m, Eᵢ ≥ 1  
    3. Distribute degrees across variables to form exponent matrix
    4. Generate coefficients and build symbolic polynomial
    
    Result: Polynomial with baseline constraint count Kbase(P) = δ
    """
    try:
        # Generate the instance
        if verbose:
            click.echo(f"Generating polynomial with δ = {delta}...")
            if seed is not None:
                click.echo(f"Using random seed: {seed}")
        
        result = generate_random_instance(
            delta=delta, 
            coeff_range=(coeff_min, coeff_max),
            seed=seed
        )
        
        # Print results
        click.echo(f"\n{'='*50}")
        click.echo(f"POLYNOMIAL GENERATION RESULTS")
        click.echo(f"{'='*50}")
        
        click.echo(f"δ (difficulty parameter): {result['delta']}")
        click.echo(f"Chosen (m, n): ({result['m']}, {result['n']})")
        
        if verbose:
            click.echo(f"\nAlgorithm steps:")
            click.echo(f"1. Chose m={result['m']} monomials, n={result['n']} variables")
            click.echo(f"2. Sampled row totals summing to {result['delta']} + {result['m']} = {result['delta'] + result['m']}")
            click.echo(f"3. Distributed degrees across variables")
            click.echo(f"4. Generated {len(result['coefficients'])} nonzero coefficients")
        
        click.echo(f"\nExponent matrix K ({result['m']}×{result['n']}):")
        _print_matrix(result['matrix'])
        
        click.echo(f"\nCoefficients: {result['coefficients']}")
        
        click.echo(f"\nSymbolic polynomial:")
        click.echo(f"P(x) = {result['polynomial']}")
        
        # Verify baseline calculation
        click.echo(f"\nVerification:")
        click.echo(f"Baseline Kbase(P): {result['baseline']}")
        if result['baseline'] == delta:
            click.echo(f"✓ Baseline matches target δ = {delta}")
        else:
            click.echo(f"✗ ERROR: Baseline {result['baseline']} ≠ target δ = {delta}")
            
        if verbose:
            click.echo(f"\nRow degrees (Eᵢ): {[sum(result['matrix'][i]) for i in range(result['m'])]}")
            row_contributions = [max(0, sum(result['matrix'][i]) - 1) for i in range(result['m'])]
            click.echo(f"Constraint contributions (Eᵢ-1): {row_contributions}")
            click.echo(f"Total: {sum(row_contributions)} = {result['baseline']}")
            
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort()


def _print_matrix(matrix: np.ndarray) -> None:
    """Pretty print a numpy matrix with proper alignment."""
    if matrix.size == 0:
        click.echo("(empty matrix)")
        return
        
    # Convert to strings for formatting
    str_matrix = matrix.astype(str)
    
    # Find max width for alignment
    max_width = max(len(s) for row in str_matrix for s in row)
    
    # Print each row
    for row in str_matrix:
        formatted_row = "  ".join(s.rjust(max_width) for s in row)
        click.echo(f"  [{formatted_row}]")


if __name__ == '__main__':
    main()