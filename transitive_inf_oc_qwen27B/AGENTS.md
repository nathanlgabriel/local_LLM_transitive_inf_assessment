# Repo: Transitive Inference Signaling Game Simulations

## Overview

Lewis–Skyrms signaling game models of the transitive inference task. Two Numba-JITted simulation backends (original + modified) driven from Jupyter notebooks. Original notebooks use `multiprocessing.Pool`; MODv2 notebooks use `concurrent.futures.ProcessPoolExecutor`.

## Files

### Original (pre-modification)

| File | Model |
|---|---|
| `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py` | Synchronous (single-urn senders) |
| `structure_ORIGINAL_FNs_2026_00.py` | Synchronous magnitudes (multi-urn, magnitude sum) |
| `structure_noiseAnn_dsktp_1s_BASElearning-MV10.ipynb` | Singleside, 1-side (`sides=1`), `pool.starmap` |
| `structure_noiseAnn_dsktp_2s_BASElearning-MV10.ipynb` | Singleside, 2-side (`sides=2`), `pool.starmap` |
| `structure_noiseAnn_dsktp_ORIGINAL_1s-MV10.ipynb` | Magnitudes, 1-side (`sides=1`), `pool.starmap` |
| `structure_noiseAnn_dsktp_ORIGINAL_2s-MV10.ipynb` | Magnitudes, 2-side (`sides=2`), `pool.starmap` |

### MODv2 (modified — reward arrays, pair stats, all-pairs eval, concurrent.futures)

| File | Model |
|---|---|
| `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_MODv2_2026.py` | Synchronous + modifications |
| `structure_ORIGINAL_FNs_2026_MODv2_00.py` | Synchronous magnitudes + modifications |
| `structure_noiseAnn_dsktp_1s_BASElearning_MODv2-MV10.ipynb` | Singleside, 1-side, `ProcessPoolExecutor` |
| `structure_noiseAnn_dsktp_2s_BASElearning_MODv2-MV10.ipynb` | Singleside, 2-side, `ProcessPoolExecutor` |
| `structure_noiseAnn_dsktp_ORIGINAL_1s_MODv2-MV10.ipynb` | Magnitudes, 1-side, `ProcessPoolExecutor` |
| `structure_noiseAnn_dsktp_ORIGINAL_2s_MODv2-MV10.ipynb` | Magnitudes, 2-side, `ProcessPoolExecutor` |

### Reference

| File | Description |
|---|---|
| `transitive_inference_modification_plan.md` | Detailed plan + implementation status |
| `reading-codebase-style-guide.md` | Guide for AI assistants reading this codebase |
| `grill-conceplentation.md` | Skill for generating conceptual understanding questions |

## Dependencies

`numpy`, `numba`. No virtual environment or lockfile — install with `pip install numpy numba`.

## Side semantics (critical)

- **Side 0** = the "second" (held-out) set. Restricts to adjacent pairs only. Test phase forces `fsides2 = [0, 0]`.
- **Side 1** = the "first" (transitively complete) set. Full pair set (adjacent + non-adjacent) when both senders read from side 1.
- In the singleside file, both senders use `fsides2[0]`. The magnitudes file uses `fsides2[0]` and `fsides2[1]` independently.
- The channel dimension `[0]` vs `[1]` in `sigweights` handles left vs right position — this is separate from side indexing.

## Key architecture

- `single_play` — one play: sender draw → receiver pick → reinforce/punish
- `nstepsfn` — training loop (numba-JIT, tight loop over `single_play`)
- `nstepsfntest` — read-only test phase (returns unmodified weights; safe to call multiple times with different pair sets)
- `play_sequence` — per-run entry point, invoked by `concurrent.futures` (MODv2) or `pool.starmap` (original)
- Receiver urn index: `leftval * (maxvalue + 1) + rightval` — encodes ordering in index topology
- Reinforcement/punishment annealing via `iterswitch` every `blocklength` steps

## MODv2 changes (vs original)

1. **Reward arrays:** `frewards2` parameter threaded through call chain; `if leftstate > rightstate:` replaced with `if left_reward == 1:`
2. **Per-pair test stats:** `pair_stats` array `(n_pairs, 2)` tracking attempts and successes per test pair
3. **All-pairs evaluation:** Second `nstepsfntest` call with `allpairs` after test phase
4. **Test phase modulus fix:** `nstepsfntest` passes `len(fpairsN)` as both `fplen` and `falen`
5. **Noise annealing floor:** `cur_noise = max(0, cur_noise - annealing)`
6. **Integer success flag:** `fcumsum2 = 0` instead of `0.`
7. **concurrent.futures:** notebooks migrated from `mp.Pool.starmap` to `ProcessPoolExecutor` with `SeedSequence` spawning
8. **Dead code cleanup:** DH mod blocks removed, commented-out code cleaned

## Numba gotchas

- All arrays passed into JIT functions must be `dtype=np.int64` (or match first-call types exactly)
- First call compiles; dtype mismatches cause recompile or fallback to object mode
- `pair_stats` and similar tracking arrays must be allocated inside JIT with explicit `numba.int64` dtype
- Variable names may not match their actual usage — trace values through the code

## Pending (not yet implemented)

1. Parametric pair generation (`make_linear_pairs` helper) for arbitrary `terms` (>5)
2. Distance / serial-position post-processing of `pair_stats`
3. Runs with `terms = 7` and beyond

## Running

Open a notebook and run top-to-bottom. MODv2 notebooks use `concurrent.futures.ProcessPoolExecutor(max_workers=thrds)` to parallelize runs. Seed entropy printed for reproducibility. Results saved as `.npy` files (sigweights, recweights, test scores, pair stats).
