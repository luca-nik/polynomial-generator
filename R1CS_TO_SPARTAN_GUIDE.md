# R1CS Circuit to Spartan2 Proof Generation Guide

This guide explains how to transform an existing R1CS circuit and generate zero-knowledge proofs using Spartan2.

## Overview

Given:
- An R1CS circuit with constraint matrices (A, B, C)
- Public inputs `x_pub`
- Public output `y_pub` at a specific position in the witness

Goal: Generate a ZK proof that the circuit computes correctly.

## Step-by-Step Implementation

### Step 1: Transform R1CS to SparseMatrix Format

Spartan2 uses its own sparse matrix format defined in `src/r1cs/sparse.rs`:

```rust
use spartan2::r1cs::{R1CSShape, SparseMatrix};

// Convert your constraint matrices to Spartan2's format
let A_sparse = SparseMatrix::new(
    your_A_matrix_rows,
    your_A_matrix_cols, 
    your_A_matrix_entries  // Vec<(row, col, value)>
);
let B_sparse = SparseMatrix::new(/* similar for B */);
let C_sparse = SparseMatrix::new(/* similar for C */);
```

### Step 2: Create R1CSShape

From `src/r1cs/mod.rs:28-47`:

```rust
let r1cs_shape = R1CSShape::<E> {
    num_cons: number_of_constraints,
    num_vars: total_variables,  // includes public inputs + witness
    num_inputs: public_input_count,  // size of x_pub
    A: A_sparse,
    B: B_sparse, 
    C: C_sparse,
};
```

### Step 3: Convert to SplitR1CSShape

Spartan2 requires the split format for efficiency (`src/r1cs/mod.rs`):

```rust
let split_shape = r1cs_shape.to_split_r1cs_shape()?;
```

### Step 4: Generate Proving and Verifying Keys

From `src/spartan.rs:114-124`:

```rust
use spartan2::spartan::{SpartanProverKey, SpartanVerifierKey};
use spartan2::provider::PallasHyraxEngine; // Choose your engine

type E = PallasHyraxEngine;

let (ck, vk) = PCS::<E>::setup(max_degree)?;  // Polynomial commitment setup
let prover_key = SpartanProverKey::new(&split_shape, &ck, &vk)?;
let verifier_key = SpartanVerifierKey::new(&split_shape, &vk)?;
```

### Step 5: Create Instance and Witness

From `src/r1cs/mod.rs:66-85`:

```rust
// Public instance (your x_pub)
let instance = R1CSInstance::<E> {
    X: your_public_inputs,  // Vec<E::Scalar> containing x_pub values
};

// Private witness 
let witness = R1CSWitness::<E> {
    W: your_full_witness,   // Vec<E::Scalar> all private variables + y_pub
};
```

### Step 6: Generate Proof

From `src/spartan.rs:200-220`:

```rust
use spartan2::spartan::R1CSSNARK;

let proof = R1CSSNARK::<E>::prove(
    &prover_key,
    &instance,    // Contains x_pub
    &witness,     // Contains all private values + y_pub at specific position
)?;
```

### Step 7: Verify Proof

From `src/spartan.rs:350-370`:

```rust
let is_valid = R1CSSNARK::<E>::verify(
    &verifier_key,
    &instance,    // Same public inputs (x_pub)
    &proof,
)?;
```

## Important Implementation Details

### Variable Ordering
The constraint system expects variables in this order:
```
z = [1, public_inputs, witness_variables]
```
Where:
- `1` is the constant term
- `public_inputs` are your `x_pub` values
- `witness_variables` include all private computations and `y_pub`

### Public Output Placement
- `y_pub` must be at the correct position in the witness vector `W`
- The R1CS constraints must enforce that this position contains the actual computation result
- The position should be known to both prover and verifier

### Constraint Format
Your R1CS matrices must satisfy: `A·z ⊙ B·z = C·z`
where `⊙` represents element-wise multiplication (Hadamard product).

### Engine Selection
Choose from available engines in `src/provider/`:
- `PallasHyraxEngine`: Pallas curve with Hyrax PCS
- `VestaHyraxEngine`: Vesta curve with Hyrax PCS
- `T256HyraxEngine`: secp256k1 curve with Hyrax PCS

## Complete Example Structure

```rust
use spartan2::{
    provider::PallasHyraxEngine,
    r1cs::{R1CSShape, R1CSInstance, R1CSWitness, SparseMatrix},
    spartan::{R1CSSNARK, SpartanProverKey, SpartanVerifierKey},
    traits::{Engine, snark::R1CSSNARKTrait},
};

type E = PallasHyraxEngine;

fn generate_proof() -> Result<(), Box<dyn std::error::Error>> {
    // Step 1-3: Create R1CS shape
    let r1cs_shape = R1CSShape::<E> { /* ... */ };
    let split_shape = r1cs_shape.to_split_r1cs_shape()?;
    
    // Step 4: Generate keys
    let (ck, vk) = /* PCS setup */;
    let prover_key = SpartanProverKey::new(&split_shape, &ck, &vk)?;
    let verifier_key = SpartanVerifierKey::new(&split_shape, &vk)?;
    
    // Step 5: Create instance and witness
    let instance = R1CSInstance::<E> { X: your_x_pub };
    let witness = R1CSWitness::<E> { W: your_witness };
    
    // Step 6: Generate proof
    let proof = R1CSSNARK::<E>::prove(&prover_key, &instance, &witness)?;
    
    // Step 7: Verify
    let is_valid = R1CSSNARK::<E>::verify(&verifier_key, &instance, &proof)?;
    
    Ok(())
}
```

## What the Proof Guarantees

The generated proof cryptographically demonstrates:
1. The prover knows private values that satisfy the R1CS constraints
2. Given the public inputs `x_pub`, the circuit produces the claimed output
3. The computation was performed correctly according to the constraint system
4. No information about the private witness values is revealed

This enables zero-knowledge verification that your R1CS circuit executed correctly with the given public inputs and produced the expected public output.