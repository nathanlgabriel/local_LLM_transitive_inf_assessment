# AGENTS.md

## Core Architecture
- **Project Goal**: Implements signaling game models for transitive inference tasks.
- **Primary Models**:
  - `structure_ORIGINAL_FNs_2026_00.py`: Synchronous magnitudes model (transmits summed magnitudes).
  - `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py`: Synchronous model (transmits ball index).
- **Execution Flow**: `Notebook` $\rightarrow$ `play_sequence` $\rightarrow$ `nstepsfn` (training) $\rightarrow$ `nstepsfntest` (testing) $\rightarrow$ `single_play` (atomic step).

## Key Logic & Semantics
- **Side Semantics**: 
  - **Side 0**: The "second" (held-out) set. Restricted to adjacent pairs.
  - **Side 1**: The "first" (complete) set. Allows all pairs (adjacent + non-adjacent).
- **Branching**: `if fsides2[0] == 0 or fsides2[1] == 0` in `single_play` enforces the restricted training condition.
- **Test Phase**: `nstepsfntest` is read-only; it must not propagate weight changes back to the caller.

## Technical Constraints
- **Numba JIT**: Core loops are JITted. 
  - **Dtype Hygiene**: Use `np.int64` for arrays passed to JIT functions to avoid recompilation or object-mode fallback.
  - **Array Allocation**: Allocate stats arrays (e.g., `pair_stats`) using `np.zeros(..., dtype=numba.int64)` inside JIT functions.
- **Randomness**: Random numbers are generated in blocks via `randoms` to optimize JIT performance.

## Known Issues & Gotchas
- **Receiver-Noise Typo**: In both `.py` files, the right-channel noise branch uses `frandunif102[0]` when it should use `frandunif102[1]`.
- **Side-Index Consistency**: The `singleside` model uses `fsides2[0]` for both senders, while the magnitudes model allows independent `fsides2[0]` and `fsides2[1]`.

## Development Roadmap
- Refer to `modification_plan.md` for the current implementation plan regarding dynamic reward structures and per-pair success tracking.
