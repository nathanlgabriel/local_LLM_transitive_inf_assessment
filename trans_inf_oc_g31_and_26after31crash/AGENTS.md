# Agents Guide: Transitive Inference Signaling Games

## Core Architecture
- **Models**: 
  - `structure_ORIGINAL_FNs_2026_00.py`: Synchronous magnitudes model (best performance, linear-ordering bias).
  - `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py`: Synchronous model.
- **Execution Flow**: `Notebook` -> `multiprocessing.starmap` -> `play_sequence` -> `nstepsfn` (training) / `nstepsfntest` (testing) -> `single_play`.
- **Performance**: Core loops are Numba JIT-compiled.

## Critical Semantics
- **Side Indices**:
  - `Side 0`: "Second" (held-out) set. Triggers adjacent-only pair sampling.
  - `Side 1`: "First" (complete) set. Allows full pair distribution sampling.
- **Test Phase**: `nstepsfntest` is strictly **read-only**. It must not propagate weight updates back to the caller.
- **Reward Logic**: Currently hard-coded as `leftstate > rightstate`.

## Development Constraints
- **Numba Hygiene**: Use `np.int64` for reward and stats arrays to avoid JIT recompilation or fallback to object mode.
- **Randoms**: Random numbers are pre-generated in blocks via `randoms()` before being passed to `single_play`.

## Known Issues
- **Receiver Noise**: Both `.py` files have a typo in the receiver-noise block where the upward perturbation on `rightval` incorrectly uses `frandunif102[0]` instead of `frandunif102[1]`.

## Verification
- **Regression**: Use the same seed and verify that output rates (training/test success) are bit-for-bit identical after refactors.
- **Dtypes**: Verify all new arrays passed to JIT functions use explicit `dtype=np.int64`.
