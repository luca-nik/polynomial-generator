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
  [2  4  3  1]
  [0  1  0  1]
  [1  4  0  1]

Coefficients: [-2.854255875884597, 0.8337578690493785, 8.901163674075413]

Symbolic polynomial:
P(x) = -2.8542558758846*x1**2*x2**4*x3**3*x4 + 0.833757869049379*x2*x4 + 8.90116367407541*x1*x2**4*x4

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

## ⚙️ Pipeline: From Polynomial to R1CS

We provide a reproducible pipeline to go from a randomly generated polynomial instance to a compiled R1CS circuit using Noir.

### Steps

### 1. Generate polynomial instance
   Use `choose_m_n(delta)` and the generator to obtain:
   - Exponent matrix `K ∈ Z^{m×n}` (exponents of variables in each monomial)
   - Coefficient vector `c ∈ F^m` (coefficients for each monomial)

   ```python
   K = [[k11, k12, ..., k1n],
        ...
        [km1, km2, ..., kmn]]  # m × n exponents

   c = [c1, c2, ..., cm]  # coefficients
  ```

### 2. Translate to Noir program
   Convert `(K, c)` into a Noir circuit that evaluates

   $$
   P(x) = \sum_i c_i \prod_j x_j^{k_{j,i}}
   $$

   and enforces `assert(y == P(x))`.

   Example generator function:

   ```python
   def generate_noir_code(K, c):
       m, n = len(K), len(K[0])

       code = """fn pow(base: Field, exp: u32) -> Field {
           let mut res = 1;
           let mut b = base;
           let mut e = exp;
           while e > 0 {
               if e % 2 == 1 { res *= b; }
               b *= b;
               e /= 2;
           }
           res
       }\n\n"""

       code += f"fn evaluate_poly(xs: [Field; {n}]) -> Field {{\n"
       code += "    let mut acc = 0;\n"
       for i in range(m):
           term = f"{c[i]}"
           for j in range(n):
               exp = K[i][j]
               if exp > 0:
                   term += f" * pow(xs[{j}], {exp}u32)"
           code += f"    acc += {term};\n"
       code += "    acc\n}\n\n"

       code += f"fn main(xs: [Field; {n}], claimed_output: Field) {{\n"
       code += "    let y = evaluate_poly(xs);\n"
       code += "    assert(y == claimed_output);\n"
       code += "}\n"
       return code
   ```

### 3. Compile Noir → R1CS
   Write the generated Noir code to `src/main.nr` inside a Noir project and compile:

   ```bash
   nargo compile --format r1cs
   ```

   This produces an R1CS JSON file (matrices `A, B, C`) inside `target/`.

### 4. Analyze compiled difficulty
   Parse the R1CS JSON to extract the actual number of constraints (`K_compiled`) and compare against δ.

---

## 🎛️ Tuning α and β

To ensure fairness across instances, we calibrate the randomization parameters (α, β) so that instances of the same δ are consistently hard for a state-of-the-art compiler (Noir).

### Calibration Protocol

1. **Fix δ** (target difficulty).
2. **Sample many pairs** `(α, β)` from the current ranges.
3. **Generate polynomials** using `(α, β)` and compile them with Noir to obtain `K_compiled`.
4. **Measure variance** of `K_compiled` across instances.
5. **Adjust ranges** `[α_min, α_max]`, `[β_min, β_max]` until variance is low and the distribution of difficulties is stable.
6. **Lock the ranges** once convergence is achieved.

### Example Pseudocode

```python
def tune_alpha_beta(delta: int, trials: int):
    results = []
    for t in range(trials):
        alpha = random.uniform(0.6, 1.5)
        beta = random.uniform(0.2, 0.8)
        K, c = generate_polynomial(delta, alpha, beta)
        noir_code = generate_noir_code(K, c)
        write_noir(noir_code)
        run("nargo compile --format r1cs")
        K_compiled = parse_r1cs("target/circuit.json")
        results.append(K_compiled)

    mu = statistics.mean(results)
    sigma2 = statistics.variance(results)
    return mu, sigma2
```


