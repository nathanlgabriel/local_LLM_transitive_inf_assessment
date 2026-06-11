# AGENTS.md

## Repository Overview

A research repository implementing three Lewis–Skyrms signaling game models of the transitive inference task. Two Python back-ends (`_2026` files) simulate the models, plus Jupyter notebooks for running experiments.

## Entry Points

**Primary execution flow:**
- Jupyter notebooks import `play_sequence` from `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py`
- The `play_sequence` function orchestrates multiprocessing runs
- Each run executes training (with reinforcement/punishment annealing) then read-only testing

**Key functions (per file):**
- `single_play`: One training play (modifies weights)
- `nstepsfn`: Training loop (calls `single_play` repeatedly)
- `nstepsfntest`: Testing loop (read-only, doesn't modify weights)
- `play_sequence`: Per-run entry point called via `multiprocessing.Pool`

## Architecture Notes

**Side semantics (critical quirk):**
- Side 0 = "second" (held-out) set, only allows adjacent pairs
- Side 1 = "first" (complete) set, allows all pairs when both senders use side 1
- Test phase hard-codes `fsides2 = [0, 0]`, forcing adjacent-only test
- Branch in `single_play`: 
  ```python
  if fsides2[0] == 0 or fsides2[1] ==0:  # adjacent pairs only
  else:                                    # all pairs (adj + nonadj)
  ```

**Multiprocessing setup:**
- `multiprocessing.Pool(processes=3)` in notebooks (hard-coded)
- Each run is independent, test phase doesn't affect weights
- Results saved as `.npy` files

**Numba JIT:**
- All core functions are `@numba.jit` decorated
- Reward arrays must be `np.int64` for type inference
- Functions use explicit loops, not fancy indexing

## Key Quirks

**Receiver-noise bug (open):**
```python
if frandunif102[1] < fnoise2:       # correct
    rightval -= 1
elif frandunif102[0] > (1-fnoise2):  # WRONG: uses left channel index
    rightval += 1
```

**Reinforcement logic (hard-coded):**
- Correct answer = larger stimulus in pair
- If left > right: reinforce when receiver picks left
- If left < right: reinforce when receiver picks right
- Current structure only supports linear-transitive reward patterns

**Annealing schedule:**
- Alternates `rein1/punish1` and `rein2/punish2` every `blocklength` plays
- `noise` also decreases during annealing phase

## Running a Single Test

1. **Open a notebook:** `structure_noiseAnn_dsktp_1s_BASElearning-MV10.ipynb`
2. **Check config:** Modify `timesteps`, `runs`, `nsteps` as needed
3. **Run:** Execute the notebook to run the full experiment

**For focused verification:**
```python
# In notebook, after importing play_sequence:
from structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026 import play_sequence

# Single run with minimal settings:
sigweights, cumsuc, cumsucadd, testcumsucadd, recweights = play_sequence(
    n=1,                    # single run
    rng=np.random.default_rng(seed=42),
    rein1=1, punish1=1,    # reinforcement settings
    rein2=1, punish2=1,
    timesteps=100, nsteps=100, sides=1,
    pairs, testpairs, nonadjpairs, allpairs, plen, alen,
    terms=5, maxvalue=10, startstop=2, noise=0.01, annealing=0,
    runs=1, inertia=1.0, blocklength=100
)
```

## Test-Only Mode

The `nstepsfntest` function is read-only:
- It captures weights as locals (`frecweightsNtest, fsigweightsNtest`)
- Returns original unmodified weights (`frecweightsN, fsigweightsN`)
- Safe to call multiple times with different pair sets

## Future Work (Modification Plan)

1. **Dynamic reward structure:** Replace hard-coded `leftstate > rightstate` comparison with data-driven `pairs_reward` arrays
2. **Per-pair tracking:** Add `pair_stats` to return attempts and successes per test pair
3. **Flexible evaluation:** Test against `allpairs` as well as `testpairs`
4. **General pair generation:** Create `make_linear_pairs()` for arbitrary `terms`

## File Ownership

- **`*_2026.py` files:** Core simulation models (two variants)
- **Notebooks:** Experimental configurations and analysis
- **`modification_plan.md`:** Detailed implementation roadmap
- **`frenchsicilian_017.pdf`:** Research paper reference

## Reproducibility

**To reproduce paper results:**
1. Use `structure_noiseAnn_dsktp_1s_BASElearning-MV10.ipynb` with `sides = 1`
2. Expected: training ≈ 0.99, test ≈ 0.572 (restricted training condition)
3. Use `structure_noiseAnn_dsktp_2s_BASElearning-MV10.ipynb` with `sides = 2`
4. Expected: test ≈ 0.602

**Key seed for replication:** Not specified (agents should ask team about experimental parameters)
