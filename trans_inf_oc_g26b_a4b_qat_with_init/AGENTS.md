# Agent Instructions

## Project Context
This repository implements simulations for Lewis–Skyrms signaling game models used in transitive inference research.

## Core Files & Models
- `structure_ORIGINAL_FNs_2026_00.py`: Implements the **Synchronous Magnitudes** model.
- `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py`: Implements the **Synchronous** model.
- Notebooks (`.ipynb`): Used for running simulations and visualizing results (primarily using the Synchronous model).

## Key Implementation Details
- **Main Entry Point**: `play_sequence` is the primary function invoked for individual runs (typically via `multiprocessing.starmap`).
- **Testing Phase**: `nstepsfntest` runs a **read-only** testing phase. It does not propagate weight updates back to the caller.
- **Side Semantics (Crucial)**:
  - **Side 0**: Represents the "second" (held-out) stimulus set. When either sender reads from Side 0, training is restricted to adjacent pairs.
  - **Side 1**: Represents the "first" (transitively complete) stimulus set.
- **Numba & Performance**:
  - Extensive use of `@numba.jit`.
  - **Constraint**: Avoid complex Python objects or high-level abstractions inside JITted functions. Use explicit loops and standard NumPy arrays.
  - **Dtype Hygiene**: When creating arrays for JITted functions (e.g., reward arrays), explicitly use `dtype=np.int64` to ensure consistent type inference.

## Workflow
- Simulations are often configured and run via Jupyter notebooks.
- Results are typically saved as `.npy` files.
