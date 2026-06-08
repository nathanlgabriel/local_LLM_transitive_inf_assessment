# AGENTS.md - Transitive Inference Signaling Game

## Model Implementation
- `structure_ORIGINAL_FNs_2026_00.py`: Synchronous Magnitudes model.
- `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py`: Synchronous model.
- **Execution**: Simulations are driven by Jupyter notebooks which import `play_sequence` and run it via `multiprocessing.starmap`.

## Core Architecture
- **Side Semantics**: 
    - Side 0: "Second" (held-out) set. Restricted to adjacent pairs.
    - Side 1: "First" (complete) set. Includes non-adjacent and test pairs.
- **Workflow**: `play_sequence` $\rightarrow$ `nstepsfn` (Training) $\rightarrow$ `nstepsfntest` (Testing).
- **Testing**: The test phase is **read-only**. `nstepsfntest` must not propagate weight updates back to the caller.

## Technical Constraints
- **Numba JIT**: 
    - Use `np.int64` for reward and statistics arrays to ensure consistent type inference and avoid fallback to object mode.
    - Keep loops explicit and avoid fancy indexing to maintain JIT performance.
- **Known Bug**: The receiver-noise block in both `.py` files contains a typo: `elif frandunif102[0] > (1-fnoise2):` should use `frandunif102[1]` to avoid coupling left and right channel noise.

## Investigation Tips
- Refer to `modification_plan.md` for the mapping between the codebase and the *Franco-Sicilian Abstraction* (Gabriel, 2025) paper.
