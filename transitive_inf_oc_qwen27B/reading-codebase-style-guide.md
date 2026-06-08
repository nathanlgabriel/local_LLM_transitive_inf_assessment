# Reading This Codebase: Style Guide for AI Assistants

## Core principle: understand what the code does, not what you think it should do

The code prioritizes computational efficiency over readability. Variable names, function names, and structural choices often reflect older framings of the problem or were chosen for speed rather than clarity. Your job is to reconstruct what the code actually implements by tracing data through its operations.

---

## 1. Names lie — usage tells the truth

Variable and function names were chosen at the time of writing and frequently describe something different from what the code actually does. The name reflects an old mental model; the code reflects the current implementation.

**Pattern A: The name describes a different abstraction layer**

A variable named to suggest a spatial or positional concept (e.g., "left" / "right" / "side") often indexes something entirely different (e.g., a dataset partition, a model variant, a temporal phase). The actual spatial distinction is handled by a different dimension of the data structure. When the name seems to suggest a meaning that contradicts the code, trace the value from allocation through its first operational use. The code is right; the name is stale.

**Pattern B: The name describes an operation that was already performed**

A variable named as if it holds a sum, count, or aggregate actually holds the per-element components. The aggregate was computed and stored in a different variable. The components are kept because they are needed downstream for per-element updates. When you see a variable that is iterated over or indexed into, it is almost certainly not a scalar despite what the name suggests.

**Pattern C: The name describes a semantic role that is irrelevant to the computation**

Parameters like `fplen` and `falen` carry labels suggesting "short list" and "long list." Inside the function they are just integer divisors used in a modulus operation. The semantic distinction doesn't matter computationally — what matters is whether the divisor covers the range of index values being produced. When you see a parameter used only in arithmetic, treat its name as a hint, not a definition.

**Rule:** Always verify the name against the code. If they disagree, the code wins.

---

## 2. Flat arithmetic indexing encodes multi-dimensional structure

Instead of dictionaries, trees, or nested lookups, multi-dimensional relationships are encoded into single integer indices using arithmetic formulas. This is faster and avoids hash overhead inside tight loops.

**Basic pattern: positional encoding**

```python
flat_idx = dim0_val * (dim1_size + 1) + dim1_val
```

This maps a pair `(dim0_val, dim1_val)` to a unique integer. The critical property is that `(a, b)` and `(b, a)` map to *different* indices when `a != b`. The ordering information is preserved in the index topology, not in any explicit comparison. Don't look for a separate ordering check — the index arithmetic encodes it.

**Generalized pattern: weighted sums across dimensions**

```python
idx = 0
for d in range(ndimensions):
    idx += draws[agent][d] * multipliers[d]
```

Each dimension contributes a weighted component. The multipliers are chosen so that different dimension combinations produce distinct flat indices. This is the same idea as positional notation (base-10: `3*10 + 5 = 35`, not `5*10 + 3 = 53`), generalized to arbitrary dimensions and non-uniform bases.

**When reading:** If you see an index computed as a product-plus-sum or weighted accumulation, ask: "What multi-dimensional space is this folding into a flat integer, and does the formula guarantee uniqueness for the intended range of inputs?"

---

## 3. Algebraic rearrangements are usually speed optimizations

The code frequently uses algebraically equivalent but computationally cheaper forms of standard operations.

**Multiplication instead of division:**

```python
# Standard approach (clearer but slower):
normalized = cumulative / cumulative[-1]
result = count(normalized < random_value)

# Code approach (faster, same discrete outcome):
threshold = cumulative[-1] * random_value
result = count(cumulative < threshold)
```

Both produce the same categorical sample. The multiplication version avoids N division operations per iteration. At 10^8+ iterations, this is meaningful.

**Other common patterns:**
- Pre-computing values outside a loop rather than recomputing
- Using integer arithmetic where floating-point would be more "correct" but the discrete outcome is identical
- Accumulating into running totals rather than recomputing from scratch

**When reading:** If the code does something that looks like an unexpected rearrangement, check whether it produces the same discrete outcome through a cheaper computational path. It almost certainly does.

---

## 4. Hard-coded values are tuned to the current experimental setup

Numbers that appear magic are often correct for the specific problem dimensions being tested. They work because the random number ranges, array sizes, and modulus operations are all aligned for that particular configuration.

**How to detect:** Look for values that are used in modulus operations, array size calculations, or random generation bounds. Ask: "If I change the problem size, does this value still cover the right range?"

**What to do:** When generalizing the code, these are the first values to parameterize. But don't flag them as bugs if they work correctly for the current setup.

---

## 5. Documentation and plans lag behind the code

Written plans, comments, and external notes often describe the state of the code at the time they were written. Fixes and improvements may have been applied to the code without updating the documentation.

**Rule:** Always check the actual source files for the current state. Treat plans and documentation as a guide to intent, not a record of implementation.

---

## 6. Asymmetry in update rules is usually intentional

If one branch of a conditional applies a floor, ceiling, or clamp and the mirror branch does not, it is typically because the mathematical properties of the operation make it unnecessary on that side.

**Example:** A punishment operation subtracts from a weight (risking going below zero), while a reinforcement operation adds (no risk of overflow at practical scales). The floor is only needed on the punishment branch. Adding a symmetric floor on the reinforcement side is unnecessary complexity, not a missing safeguard.

**When reading:** Before flagging asymmetry as a bug, check whether the operations on each branch have different risk profiles. If one side can go negative and the other can't, the asymmetry is correct.

---

## 7. Verify modifications are bit-for-bit equivalent before changing behavior

When modifying code that claims to preserve existing behavior, validate with the same random seed producing identical output. A substitution like replacing a hard-coded comparison with a data-driven lookup should produce identical results when the data is constructed to match the original comparison. This regression check should pass before adding new functionality.

---

## 8. Walk through a complete cycle to verify understanding

Before modifying the code, trace one complete execution cycle:

1. What inputs does the entry point receive?
2. How are random numbers consumed?
3. What decision is made at each branch?
4. Which arrays are read, which are modified?
5. What is returned, and what is discarded?

If you can't trace a single cycle without guessing at a variable's meaning, re-read the relevant section. The code is deterministic given the same random seed — follow the data.
