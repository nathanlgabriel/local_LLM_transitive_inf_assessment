# Plan for Modifying the Transitive Inference Signaling Game Code

This document maps the existing Python files and notebooks onto the models described in *Franco-Sicilian Abstraction* (Gabriel, April 2025), then describes two desired modifications in prose, and finally lays out a concrete plan for implementing those modifications while preserving the existing structure and style of the code.

---

## Implementation status (updated May 2026)

**Completed:**

- [x] **Reward arrays.** `frewards2` parameter threaded through `single_play`, `nstepsfn`, `nstepsfntest`, and `play_sequence` in both `.py` files. The `if leftstate > rightstate:` comparison replaced with `if left_reward == 1:`. Reward arrays built in notebooks with `dtype=np.int64`. Bit-for-bit equivalent when rewards derived from `a > b` rule.
- [x] **Per-pair test stats.** `pair_stats` array of shape `(len(fpairsN), 2)` allocated inside `nstepsfntest` with `dtype=numba.int64`. Column 0 = attempts, column 1 = successes. Returned from `nstepsfntest` and `play_sequence`. Notebooks capture and print per-pair accuracy.
- [x] **All-pairs evaluation.** Second `nstepsfntest` call in `play_sequence` with `allpairs`/`allpairs_reward`. Returns `evalcumsucadd` and `eval_pair_stats`. Printed and saved in notebooks.
- [x] **Test phase modulus fix.** `nstepsfntest` now passes `len(fpairsN)` as both `fplen` and `falen` to `single_play`, bypassing the side-based branch. Comment added explaining the choice.
- [x] **Noise annealing floor.** `noise` variable renamed to `cur_noise` in `play_sequence` with `max(0, cur_noise - annealing)` floor.
- [x] **Integer success flag.** `fcumsum2` initialized as `0` (not `0.`) in `single_play`. The `+= 1` still produces int-compatible values.
- [x] **concurrent.futures migration.** Notebooks migrated from `mp.Pool.starmap` to `concurrent.futures.ProcessPoolExecutor`. `SeedSequence` entropy printed for reproducibility. `numba.typed.List` used for RNG array. Results keyed by run ID.
- [x] **Dead code cleanup.** DH mod commented-out blocks removed from both `.py` files. Commented-out sender-noise and update lines cleaned from singleside file.

**Remaining:**

(All items completed. See additional completed items below.)

- [x] **Parametric pair generation (`make_linear_pairs`).** Helper function in all 4 MODv2 notebooks generates pairs/rewards for arbitrary `terms`. Non-adjacent pairs with at least one endpoint go to training; non-adjacent interior pairs go to test. Validated for `terms=5` (20 pairs, 2 test) and `terms=7` (42 pairs, 12 test).
- [x] **Distance / serial-position post-processing.** All 4 MODv2 notebooks have 4 aggregation cells: (1) test accuracy by distance, (2) all-pairs eval accuracy by distance, (3) test accuracy by endpoint positions, (4) all-pairs eval accuracy by endpoint positions.
- [x] **`nsteps_eval` parameter.** Separate evaluation sample size added to `play_sequence` (both `.py` files) and all notebooks. Default `nsteps_eval=500` for terms=5, `nsteps_eval=2100` for terms=7.
- [x] **Move to `terms = 7`.** `structure_noiseAnn_dsktp_1s_BASElearning_MODv2-MV10.ipynb` updated to `terms=7` with `nsteps_eval=2100`. Produces 12 test pairs at distances 2, 3, 4. All 42 ordered pairs covered.

---

## 1. The paper at a glance

The paper presents three Lewis–Skyrms signaling game models of the transitive inference task plus a fourth model of a nonsense-grammar task. The transitive inference setup uses two serially ordered stimulus sets — capital letters A, B, C, D, E and lowercase letters a, b, c, d, e — and asks whether an agent trained on adjacent and (selectively) non-adjacent pairs can correctly choose the larger element of a held-out non-adjacent pair.

The three transitive-inference models are:

1. **Diachronic model (§3.1).** Two phases. Phase 1 trains agents on every distinct pair of the first set (adjacent *and* non-adjacent). Phase 2 trains on only adjacent pairs of the second set, but reuses the receiver urns from Phase 1 by routing the second-set stimuli through a new intermediate layer of urns. Performance reported as a stepping stone; it is the conceptual scaffold for the other two models.

2. **Synchronous model (§3.2).** A single training phase. Both stimulus sets are present simultaneously, with cross-pairings (e.g. B-c) allowed. Non-adjacent pairs are trained *only* when both stimuli come from the first set. Each sender has one urn per stimulus, with `maxvalue` ball types per urn. The transmitted signal is the index of the drawn ball.

3. **Synchronous magnitudes model (§3.3).** Same training setup as the synchronous model, but each sender has *M* urns per stimulus, each urn starting with one "0 ball" and one "1 ball". The sender draws from every urn and transmits the *sum*, i.e. a magnitude in [0, M]. This is the model that performs best on transfer to the held-out non-adjacent pair, and is the one that exhibits the linear-ordering bias discussed in §6.

The nonsense-grammar model (§5) generalizes the synchronous architecture to three senders and a four-way receiver decision; it is not currently in the codebase shared with me.

---

## 2. The files

### 2.1 The two `.py` files (post-2026 corrections)

There are two simulation back-ends, each implementing one of the paper's transitive-inference models.

#### `structure_ORIGINAL_FNs_2026_00.py` — the **synchronous magnitudes model**

Sender weight array:

```python
sigweights = inertia * np.ones([sides, 2, terms, maxvalue, startstop])
```

The final `startstop = 2` dimension is the "0 ball / 1 ball" pair inside each of the `maxvalue` urns associated with each stimulus. Inside `single_play`, for each of those `maxvalue` urns the code samples whether a 0 ball or 1 ball was drawn (using the per-urn random vector `frandunif22` / `frandunif42`), the boolean draws are summed, and that integer is the magnitude transmitted to the receiver. The receiver indexes its urn by `leftval * (maxvalue + 1) + rightval` and picks left or right.

This file also has the optional sender-noise step active (the `leftnoise`/`rightnoise` block), which flips individual urn outputs with probability `fnoise2`.

#### `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2_2026.py` — the **synchronous model**

Sender weight array:

```python
sigweights = inertia * np.ones([sides, 2, terms, maxvalue])
```

There is no `startstop` dimension here. Each stimulus has one urn with `maxvalue` ball types. Sampling uses `np.cumsum(leftweights)` against a single uniform `frandunif22`, and `leftval` is the index of the drawn ball type. The sender-noise block is commented out.

The "singleside" naming reflects a second design choice: both sender lookups use `fsides2[0]`,

```python
leftweights  = (fsigweights2[fsides2[0]][0][leftstate]).copy()
rightweights = (fsigweights2[fsides2[0]][1][rightstate]).copy()
```

so each play uses a single side-index for both senders. By contrast, `_FNs_2026_00.py` uses `fsides2[0]` and `fsides2[1]` independently, allowing genuine cross-set pairings during simultaneous training.

#### Shared structure of both files

Both files share the same function decomposition:

- **`single_play`** does one play: pick a pair via `stateidx`, have each sender draw and transmit, have the receiver pick, then apply reinforcement or punishment to all of the urns that were used.
- **`randoms`** generates one block's worth of random numbers in advance (state-of-nature indices, side indices, and the various uniform vectors needed by `single_play`).
- **`nstepsfn`** runs `nsteps` training plays in a tight numba-JITted loop.
- **`nstepsfntest`** is the testing counterpart: it runs `nsteps` plays with `fsides2` hard-coded to `[0, 0]` and `fpairsN` set to the test pair array, and crucially it does *not* propagate the post-test weights back to the caller (the test phase is read-only).
- **`play_sequence`** is the per-run entry point invoked by `multiprocessing.starmap`. It initializes `sigweights` and `recweights`, runs the training loop (with an optional reinforcement/punishment annealing schedule via `iterswitch`), then runs the test phase.

#### Two corrections that were just made

Two issues in the older versions were fixed in the `_2026` files:

1. The condition `fsides2[0] == 0 or fsides2[0] == 0` in the singleside file was a typo for `fsides2[0] == 0 or fsides2[1] == 0`. Now corrected, matching the magnitudes file.

2. In the receiver-update branches, the "wrong choice" case used to apply `fpunish2` to the receiver weight associated with the *correct* action instead of the *chosen* action. Both files now punish the chosen receiver weight on a wrong pick, with the floor of 1 preserved. Reinforcement-with-punishment is now symmetric.

#### One issue still present

The receiver-noise block contains a typo:

```python
if frandunif102[1] < fnoise2:
    rightval -= 1
    ...
elif frandunif102[0] > (1-fnoise2):     # should be frandunif102[1]
    rightval += 1
    ...
```

The downward perturbation on `rightval` correctly uses index `[1]`, but the upward perturbation uses index `[0]`, which couples the right-channel's "+1 noise" to the left channel. Currently inert because all notebooks set `noise = 0`, but it should be fixed before any noise sweep is run. (Both files have this; one-character fix in each.)

### 2.2 The two notebooks

Both notebooks import `play_sequence` from `structure_ORIGINAL_FNs_singlesideBASEreinLEARNING2`, so they run the **synchronous model** (single-urn senders), not the magnitudes model.

- **`structure_noiseAnn_dsktp_1s_BASElearning-MV10.ipynb`** sets `sides = 1`. Only side 0 exists, so only adjacent pairs are ever trained (the "restricted training" condition of §3.4 — train only on adjacent pairs of one set, test on B-D / D-B). Result: training cumsucadd ≈ 0.99, test cumsucadd ≈ 0.572. This is the synchronous-model analogue of the 0.6217 figure the paper reports for restricted training.

- **`structure_noiseAnn_dsktp_2s_BASElearning-MV10.ipynb`** sets `sides = 2`. Both side 0 (the held-out "test" set) and side 1 (the "first" set, trained on all pairs) are present. Cross-set pairings are allowed but reduced to adjacent only. Result: test cumsucadd ≈ 0.602.

The notebooks also include a post-hoc cell counting how many runs produced sender strategies in which the same `(leftval, rightval)` magnitude pair encodes two distinct stimulus pairings (`runs_dup_bins`). This corresponds to the combinatorial discussion in footnotes 6–7 of the paper.

### 2.3 Side semantics — how the code encodes "first set" vs "second set"

This is the part most likely to confuse anyone reading the code cold. The branch in `single_play`,

```python
if fsides2[0] == 0 or fsides2[1] == 0:
    stateidx = fstate2 % fplen2          # adjacent pairs only
else:
    stateidx = fstate2 % falen2          # all pairs (adj + nonadj + test)
```

together with `allpairs = np.concatenate((pairs, nonadjpairs, testpairs))` and the test phase passing `fsides2 = [0, 0]`, encodes the following:

- **Side 0 is the "second" (held-out) set.** Whenever either sender is reading from side 0, the play is restricted to adjacent pairs. Testing forces both sides to 0, so only the `testpairs` array is sampled.
- **Side 1 is the "first" (transitively complete) set.** Only when *both* senders are reading from side 1 does the full `allpairs` array — including non-adjacent and test pairs — get drawn from.

In the 2-side notebook these two roles interleave randomly: each play picks `naturesides[i] ∈ {0,1}²` uniformly, giving four equally likely conditions per play.

---

## 3. The two desired modifications

### 3.1 Modification 1 — dynamic specification of which item in a pair is rewarded

Right now, "the correct answer is the larger of the two stimuli" is hard-coded inside `single_play` as

```python
if leftstate > rightstate:
    # reinforce when receiver picked left
else:
    # reinforce when receiver picked right
```

This forces the model into a single linear-transitive structure. To run circular orderings, rock-paper-scissors, reverse-on-nonadjacent, or any other custom reward structure, one currently has to edit the function. The desired change is to make the reward structure data, not code: alongside each `*pairs` array, supply a same-shaped `*pairs_reward` array whose entries are 0/1, with a 1 marking the position in the pair that should be reinforced when chosen.

For example, the current setup is equivalent to

```python
pairs        = np.asarray([[0,1],[1,0],[1,2],[2,1],[2,3],[3,2],[3,4],[4,3]])
pairs_reward = np.asarray([[0,1],[1,0],[0,1],[1,0],[0,1],[1,0],[0,1],[1,0]])
```

For a circular ordering on five elements one would additionally include

```python
testpairs        = np.asarray([[0,4],[4,0]])
testpairs_reward = np.asarray([[1,0],[0,1]])
```

and so on. The inner code becomes a lookup rather than a comparison.

### 3.2 Modification 2 — measuring distance effects on the test pairs and beyond

In the comparative-psychology literature on transitive inference, two empirical signatures are commonly reported:

- **Symbolic distance effect**: accuracy on a test pair tends to increase as the distance between the two stimuli in the serial order increases. With five elements and one held-out distance-2 pair (B-D), this can't really be seen — the current notebooks have only two test pairs, both distance 2.
- **Serial position effect**: accuracy depends on where in the ordering the two stimuli sit (e.g. pairs anchored at the extremes are easier).

To measure these properly we need:

1. **Longer sequences.** Concretely, planned runs with `terms = 7` and possibly larger. The `terms` parameter already drives the size of `sigweights`, so the sender side is parameterized; what is currently hard-coded is the *contents* of `pairs`, `testpairs`, and `nonadjpairs`. These need to be generatable for arbitrary `terms`.
2. **Per-pair success counts at test time**, rather than a single aggregate `testcumsucadd`. With those counts in hand, computing accuracy as a function of stimulus-pair distance (or stimulus-pair endpoints, for serial position) becomes a post-processing exercise.
3. **A way to evaluate on all pairs, not just the held-out test set.** The user wants to be able to see distance effects across the full pair distribution, not only on the two-element `testpairs` slot. This means either calling the testing function with an alternate pair set (such as `allpairs`) or factoring the testing into a function that takes any pair array.

The reward arrays from Modification 1 are a prerequisite for (3): if we want to evaluate on `allpairs`, we need to know which side of each pair is rewarded.

---

## 4. Implementation plan

The plan is to introduce the reward arrays first, then add per-pair tracking, then expose flexible-pair-set evaluation, all while keeping the existing numba style (explicit loops, integer dtypes, no fancy indexing).

### 4.1 Reward arrays — threading through the call stack

**Notebook level.** Author `pairs_reward`, `nonadjpairs_reward`, `testpairs_reward` next to each existing array, and concatenate them in the same order:

```python
allpairs        = np.concatenate((pairs, nonadjpairs, testpairs))
allpairs_reward = np.concatenate((pairs_reward, nonadjpairs_reward, testpairs_reward))
```

For convenience, a one-liner builds the standard linear-transitive case from any `pairs` array:

```python
pairs_reward = np.asarray([[1,0] if a > b else [0,1] for a,b in pairs],
                          dtype=np.int64)
```

**`single_play` signature.** Add one new array parameter, `frewards2`, sitting alongside `fpairs2` in the argument list. Inside the function, after computing `stateidx`, look up the reward:

```python
leftstate     = fpairs2[stateidx][0]
rightstate    = fpairs2[stateidx][1]
left_correct  = frewards2[stateidx][0]
right_correct = frewards2[stateidx][1]
```

Then the branching condition that used to read `if leftstate > rightstate:` becomes `if left_correct == 1:`. Everything inside the branches stays exactly the same. This is a literal substitution: when `pairs_reward` is built from the `a > b` rule, the function's output is bit-for-bit identical to the existing behavior. The substitution should be applied in both `.py` files.

**`nstepsfn` and `nstepsfntest`.** Each gains a new parameter, `fpairsRewN`, that gets forwarded to `single_play`. No other logic changes.

**`play_sequence`.** Its signature grows to take `pairs_reward`, `nonadjpairs_reward`, `testpairs_reward`, `allpairs_reward`. The training call forwards `allpairs_reward`, the test call forwards `testpairs_reward`.

**Notebook starmap call.** The argument tuple in `pool.starmap(...)` gets four new entries inserted, matching the new `play_sequence` signature. (Keeping the new arguments grouped with their pair counterparts keeps the call readable.)

**Numba dtype hygiene.** Build every reward array with `dtype=np.int64` so the JIT type inference sees the same dtype as `allpairs`. `numba.jit` infers types from the first call; sloppy dtypes here will cause a needless recompile or, worse, a fallback to object mode.

### 4.2 Per-pair success tracking at test time

The test function currently returns just `fcumsumNtest`. Augment it with a `pair_stats` array of shape `(len(fpairsN), 2)`, where column 0 holds attempts and column 1 holds successes for each test pair. The body of the loop gains two lines:

```python
stateidx = fstateN % len(fpairsN)        # already computed by single_play, but cheap
# ... single_play call as before, returning fcumsumaddtest ...
pair_stats[stateidx, 0] += 1
pair_stats[stateidx, 1] += int(fcumsumaddtest)
```

`pair_stats` is returned alongside the existing return values. The caller (`play_sequence`) receives it and includes it in its return tuple. The notebook unpacks an extra list,

```python
final_test_pair_stats = np.asarray(
    [r[5] for r in mpseq_final]
)   # shape (runs, n_test_pairs, 2)
```

and post-processes it. Distance is computed in Python, not in numba, so the user can swap the distance metric freely:

```python
distances = np.abs(testpairs[:, 0] - testpairs[:, 1])      # linear
# or:  distances = np.minimum(d, terms - d)                 # circular
```

Aggregating by distance is then a few lines of numpy: for each unique distance, sum attempts and successes across the matching pair indices and divide. This is enough to detect both symbolic-distance and serial-position effects (the latter by grouping on pair endpoints rather than `abs(a-b)`).

**Training-phase tracking, optionally.** The same `pair_stats` augmentation can be applied to `nstepsfn` if a per-pair learning curve is wanted. With `timesteps = 10^8` and `nsteps = 100`, recording stats every block would produce a (10^6, n_pairs, 2) array per run — too big. A reasonable middle ground is to track *only the last K blocks* (e.g. K = 100, so the final 10,000 plays), or to record snapshots at log-spaced intervals. I would defer this until the test-phase version is working and the notebook plumbing is in place.

### 4.3 Evaluation on all pairs, not just held-out test pairs

With the per-pair stats machinery in place, this is essentially free: after the existing test call, run a second `nstepsfntest` with `allpairs` and `allpairs_reward` instead of `testpairs` and `testpairs_reward`. The function does not modify weights (it returns the input `frecweightsN, fsigweightsN`, not the test-locals), so back-to-back calls are safe.

Two small considerations:

- **Sample size.** The current test call uses `nsteps = 100` plays for 2 test pairs (≈50 plays per pair). With `terms = 7` and an "all pairs" sweep, there are 42 ordered pairs; 100 plays gives ≈2.4 per pair, which is too few for a stable per-pair rate. Use a separate `nsteps_eval` parameter — something like `nsteps_eval = 50 * len(allpairs)` — for the all-pair sweep, and regenerate the random arrays accordingly.
- **`% fplen` versus `% falen` in `single_play`.** When the test call hard-codes `fsides2 = [0, 0]`, the function takes the "adjacent only" branch and uses `fplen2`. During the all-pair sweep, we want `falen2`. The simplest fix is to pass `len(fpairsN)` as *both* `fplen2` and `falen2` from `nstepsfntest`, since the test phase always operates on whatever array it was handed. (The branch then doesn't matter.) This is a small but important detail for a clean refactor.

### 4.4 Generalizing pair generation for arbitrary sequence length

`terms` already parameterizes the sender weight arrays, but the contents of `pairs`, `nonadjpairs`, and `testpairs` are hand-written for the five-element case. For seven or more elements, generate them:

```python
def make_linear_pairs(n_stim, hold_out=None):
    """
    n_stim    : number of stimuli (terms)
    hold_out  : iterable of (i, j) tuples to reserve as test pairs;
                if None, only the canonical B-D / D-B analogue is held out.
    Returns: adjpairs, nonadjpairs, testpairs, and matching reward arrays
             (higher index = rewarded, the standard linear-TI rule).
    """
```

The reward arrays are computed inside the helper with the `[1,0] if a > b else [0,1]` rule. The helper lives in the notebook (not the `.py`), so the `.py` stays agnostic about which orderings are meaningful. Circular and other variants would have their own analogous helpers or be hand-written.

`terms` itself flows through to `sigweights` correctly already. `recweights` is sized by `(maxvalue + 1)^2`, independent of `terms`, so no change is needed there.

### 4.5 Suggested implementation order

1. **`.py` refactor.** Add `frewards2` to `single_play` and replace the `>` comparison. Add `fpairsRewN` to `nstepsfn` and `nstepsfntest`. Add `pair_stats` to `nstepsfntest`. Pass `len(fpairsN)` for both `fplen` and `falen` in the test call. Update `play_sequence`'s signature and internal calls. Do this once in each of the two `.py` files, and confirm that the existing five-element notebook produces statistically equivalent training and test rates to the pre-refactor version (this is the regression check). Same seed → same result, since the substitution is exact.

2. **Notebook helper.** Add `pairs_reward`, `nonadjpairs_reward`, `testpairs_reward`, `allpairs_reward`, and (when ready) `make_linear_pairs` for arbitrary `terms`. Extend the `pool.starmap` argument tuple to include the four reward arrays.

3. **Per-pair test output.** Capture `pair_stats` from each run. Save it alongside the existing `_sigweights`, `_recweights`, `_testcumsucadd` `.npy` files.

4. **Distance / serial-position post-processing.** Compute `distances = |testpairs[:,0] - testpairs[:,1]|`, aggregate `pair_stats` across runs grouped by distance, and report mean accuracy and standard error per distance bucket. The same code, run against an `allpairs_stats` array, gives the full distance spectrum.

5. **Move to `terms = 7` (and beyond).** With pair generation now parametric, the change is `terms = 7` in the configuration cell plus calling `make_linear_pairs(7, ...)`. Decide which non-adjacent distances to withhold as test pairs and which to include in training — this is now a notebook-level decision.

6. **Mirror everything in the magnitudes file.** Once the singleside file is working end-to-end and validated, apply the same edits to `structure_ORIGINAL_FNs_2026_00.py`. The synchronous-magnitudes model is the one the paper claims has the linear-ordering bias, so it's the model the distance-effect runs ought to use eventually.

### 4.6 Things to be careful about

- **Numba type inference.** Reward arrays must be `np.int64` and shaped `(n_pairs, 2)`. `pair_stats` should be allocated as `np.zeros((..., 2), dtype=numba.int64)` inside the JITted function (consistent with the existing pattern in `runs_dup_bins`).
- **The test function is read-only.** This is the property that lets us evaluate against multiple pair sets in a single run without contaminating the weights. The refactor must preserve it. Concretely: inside `nstepsfntest`, the call captures `frecweightsNtest, fsigweightsNtest` as locals but returns the unmodified `frecweightsN, fsigweightsN`. Keep that pattern.
- **Random number consumption.** `randoms` returns `frandunif2` and `frandunif4` whose width is `fmaxvalue1`. In the singleside file these are only used as scalars (the first element), so increasing `terms` doesn't affect random-number consumption here, but for the magnitudes file the full width is consumed. Worth noting if reproducibility across `terms` settings matters.
- **The hard-coded `[0, 0]` test side.** The test phase always reads from side 0. With `sides = 2` this means the test pair stimuli are evaluated through the side-0 sender weights, which (in the synchronous condition) have only ever been exposed to adjacent pairs of their set. That's by design — that *is* the transfer-learning probe — but it's worth re-confirming this is still the right behavior for the new distance-effect experiments. If you want to also probe side 1's weights, that'd be a separate call with `fsides2 = [1, 1]`.
- **Receiver-noise typo (still open).** `elif frandunif102[0] > (1-fnoise2):` in the right-channel branch should be `frandunif102[1]`. Trivial fix to apply during the same refactor pass.

---

## 5. What this plan deliberately leaves alone

- The receiver-urn indexing scheme `leftval * (maxvalue + 1) + rightval`.
- The annealing / `iterswitch` reinforcement schedule.
- The `multiprocessing.Pool(processes=3)` setup in the notebooks.
- The duplicate-bins analysis cell.
- The save-as-`.npy` convention.

These are independent of the two modifications and there is no reason to touch them. The intent is to layer the reward arrays and the per-pair tracking on top of the existing code rather than rewrite around them.
