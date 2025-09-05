# Random Polynomial Generator

A Python implementation of a random polynomial instance generation algorithm. This tool generates multivariate polynomials with a specified baseline difficulty parameter δ that corresponds to the number of R1CS constraints needed for naive polynomial evaluation.

## 🎯 Purpose

This generator creates random polynomial functions for benchmarking and testing R1CS circuit optimization techniques. Given a single difficulty parameter δ, it produces:

- **Random multivariate polynomial** with controllable complexity
- **Exponent matrix representation** for analysis  
- **Symbolic mathematical form** for verification
- **Guaranteed baseline constraint count** equal to input δ

## 📦 Installation

Clone the repo, then:
```bash
cd polynomial-generator
poetry install
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic usage - generate polynomial with difficulty δ=15
poetry run python -m polynomial_generator.cli --delta 15

# With reproducible seed
poetry run python -m polynomial_generator.cli --delta 20 --seed 42

# Verbose output showing algorithm steps
poetry run python -m polynomial_generator.cli --delta 25 --verbose

# Custom coefficient range
poetry run python -m polynomial_generator.cli --delta 10 --coeff-min 1 --coeff-max 5
```

#### Example Output
```
==================================================
POLYNOMIAL GENERATION RESULTS
==================================================
δ (difficulty parameter): 15
Chosen (m, n): (3, 4)

Exponent matrix K (3×4):
  [2  1  0  3]
  [1  2  1  0]  
  [0  1  1  2]

Coefficients: [5, -3, 7]

Symbolic polynomial:
P(x) = 5*x1**2*x2*x4**3 - 3*x1*x2**2*x3 + 7*x2*x3*x4**2

Verification:
Baseline Kbase(P): 15
✓ Baseline matches target δ = 15
```

## 🧮 Algorithm

The implementation follows Section 2.4 of the paper:

1. **Choose sizes**: Automatically select number of monomials `m` and variables `n` based on δ
   - `m ∈ [1, min(δ, ⌊√δ⌋ + 5)]`
   - `n ∈ [2, min(δ, m+3, 10)]`

2. **Set row totals**: Sample positive integers `(E₁, ..., Eₘ)` where:
   - Each `Eᵢ ≥ 1` (minimum monomial degree)  
   - `∑Eᵢ = δ + m` (ensures baseline equals δ)

3. **Form monomials**: For each row i, distribute degree `Eᵢ` across n variables:
   - Creates exponent vector `(k₁,ᵢ, ..., kₙ,ᵢ)` with `∑kⱼ,ᵢ = Eᵢ`
   - Uses Dirichlet distribution for balanced variable participation
   - Allows zero exponents (variables can be absent)

4. **Generate coefficients**: Random nonzero integers from specified range

5. **Build polynomial**: Construct symbolic expression `P(x) = ∑cᵢ∏xⱼ^(kⱼ,ᵢ)`

**Key Property**: The resulting polynomial has baseline constraint count `Kbase(P) = ∑(Eᵢ - 1) = δ`

## 📊 Output Formats

### Exponent Matrix K
The core representation is an `m×n` integer matrix where `K[i,j] = kⱼ,ᵢ` is the exponent of variable `j` in monomial `i`.

```python
# Example: 3 monomials, 4 variables
matrix = array([
    [2, 1, 0, 3],  # x₁²x₂x₄³  (degree=6)
    [1, 2, 1, 0],  # x₁x₂²x₃   (degree=4) 
    [0, 1, 1, 2]   # x₂x₃x₄²   (degree=4)
])
```

### Symbolic Polynomial
Human-readable mathematical expression using SymPy:
```python
P(x) = 5*x1**2*x2*x4**3 - 3*x1*x2**2*x3 + 7*x2*x3*x4**2
```

### Baseline Verification
Automatic verification that `Kbase(P) = δ`:
```
Row degrees: [6, 4, 4]
Contributions: [5, 3, 3]  # Each (degree - 1)
Total baseline: 11 = δ
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run specific test modules  
poetry run pytest tests/test_instance_generator.py
poetry run pytest tests/test_chooser.py
poetry run pytest tests/test_cli.py

# Run with coverage
poetry run pytest --cov=polynomial_generator
```
