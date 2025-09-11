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

1. **Choose sizes (m, n)**: We use a randomized heuristic parameterized by δ:
   - Sample `α ~ Uniform(0.6, 1.5)` and `β ~ Uniform(0.2, 0.8)`
   - Set `m = max(1, ⌊α·√δ⌋)` (controls density)
   - Set `n = max(2, ⌊√δ / β⌋)` (keeps growth sublinear)
   - The optional `seed` parameter makes these choices reproducible.
   - `validate_m_n` checks feasibility under `∑Eᵢ = δ + m` with `Eᵢ ≥ 1`.

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

## 📐 Polynomial Instance Generation

We generate random polynomial instances parameterized by a target baseline difficulty `δ`.
Each instance is represented by a coefficient vector `c ∈ F^m` and an exponent matrix
`K ∈ Z_{≥0}^{m×n}`, defining:

`P(x) = \sum_{i=1}^{m} c_i \prod_{j=1}^{n} x_j^{k_{j,i}}`.

To choose the number of monomials `m` and variables `n`, we use:

- `m = ⌊α · δ⌋`, `n = ⌊√δ / β⌋`, with `α ~ U(0.6, 1.5)` and `β ~ U(0.2, 0.8)`.
- √δ scaling keeps growth sublinear so circuits remain tractable at large δ.
- `α` controls density: larger `α` → more monomials (denser polynomials).
- `β` controls width/depth tradeoff: smaller `β` → more variables with shallow exponents (wide), larger `β` → fewer variables with higher exponents (deep).

This creates natural diversity in structure while keeping instances of the same δ comparable.

### Protocol for Calibrating α and β

We use a calibration loop with a state-of-the-art compiler (e.g., Noir) to ensure fairness:

1. Fix δ (baseline difficulty).
2. Sample candidate values of `α`, `β` in their ranges.
3. Generate many random polynomials using these `α`, `β`.
4. Compile each polynomial with Noir to obtain actual compiled constraint count `K_compiled`.
5. Measure variance of `K_compiled` across instances.
6. Tune `α`, `β` ranges so that, for fixed δ, the distribution of compiled constraint counts has low variance (i.e., “fair hardness” regardless of instance shape).
7. Lock parameters once distributions stabilize.

This protocol aims to guarantee that for any fixed δ, a randomly chosen instance is consistently “equally hard” for a modern compiler, even if its internal structure differs (wide vs deep).

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
