# Grill-Conceplentation Skill

## Purpose

Build conceptual understanding of a codebase by generating and resolving questions about how the code algorithmically implements its intended behavior. Focus on whether the code correctly represents what it is supposed to represent, and whether efficiency-driven patterns are working as intended.

## When to use

- Starting work on a new project from this codebase
- Before implementing modifications, to verify understanding
- When efficiency-driven code patterns seem opaque

## Question categories

### Name-vs-usage mismatches

Variable or function names describe something different from how the code actually uses them. The name reflects an older framing; the code reflects the current implementation.

**Prompt:** "X is named as if it represents [A], but the code uses it as [B]. Is the name stale?"

**Look for:** names suggesting spatial, positional, or semantic roles that don't match the code's operations. Trace values from allocation through first use.

### Indexing and encoding schemes

Multi-dimensional data is folded into flat integer indices using arithmetic. The index topology encodes relationships that might otherwise be represented with separate structures.

**Prompt:** "Index Z is computed as [formula]. What multi-dimensional space does this map into, and does the formula guarantee uniqueness for the intended input range?"

**Look for:** positional encoding (`a * (N+1) + b`), weighted sums across dimensions, any arithmetic that packs multiple values into one integer.

### Computational efficiency choices

Algebraically equivalent rearrangements and pre-computed values replace more readable but slower approaches.

**Prompt:** "The code does [A] instead of the more standard [B]. Is this a speed optimization, and does it produce the same discrete outcome?"

**Look for:** multiplication-in-place-of-division, pre-batched random numbers, manual accumulation instead of built-in functions, algebraic rearrangements that avoid expensive operations inside tight loops.

### Hard-coded values and generalization

Magic numbers are tuned to the current problem dimensions. They work for the existing setup but will break when parameters change.

**Prompt:** "Value X is hard-coded to Y. Does this depend on the current problem size, and what breaks if we change Z?"

**Look for:** values in modulus operations, random generation bounds, array size calculations tied to specific input dimensions.

### Model-fidelity questions

The code may implement a mechanism correctly but introduce unintended artifacts, or it may implement something different from the intended model. A common variant is **phase semantics**: a function or code block is supposed to operate in a specific mode (e.g., "read-only test", "training with side 0 only"), but the configuration passed to it doesn't enforce that mode.

**Prompt:** "This code block is supposed to do [phase purpose, e.g., 'test side-0 transfer performance']. Does the configuration actually enforce that purpose, or does it accidentally mix in something else?"

**Look for:** test/evaluation phases that should use fixed parameters but instead use runtime-sampled values, phases that should operate on a subset of data but use the full set, functions whose docstring or comment describes one behavior but whose parameters allow a different one. When a phase has a semantic label (train/test/eval), verify every parameter actually supports that label.

### Structural asymmetry

One branch of a conditional applies an operation that the mirror branch does not. This is usually intentional (different risk profiles) but occasionally a bug.

**Prompt:** "Operation X is applied in branch A but not branch B. Is this intentional because the operations have different risk profiles, or is it a missing mirror?"

**Look for:** floors/ceils on one side, updates touching one array but not its counterpart, conditions referencing only one element of a pair.

### Data ownership and mutation

Functions may modify their inputs in place rather than returning new values. This is especially dangerous when the same data structure is used across multiple phases (e.g., training, testing, evaluation), where a later phase silently operates on data contaminated by an earlier phase.

**Prompt:** "Function F takes array A as input and returns array B. Is B the same object as A (mutated in place) or a copy? If in-place, does the caller expect mutation, or will later code silently operate on contaminated data?"

**Look for:** functions that assign into input arrays (`arr[idx] = ...`), callers that reassign returned values expecting clean state (`a, b = fn(a, b)`), multi-phase pipelines where later phases should start from unmodified inputs. In NumPy, arrays are always passed by reference; `.copy()` is required to isolate phases.

### Parameter propagation through call chains

A value passed to a function is transformed into something that constrains downstream behavior (e.g., an integer range that determines how many distinct indices can be sampled). The value may be correct for one configuration but silently wrong for another.

**Prompt:** "Value X is passed to function F, which generates data in range [A, B). Downstream code expects data covering [C, D). Does the range actually cover what's needed, or are some indices never reached?"

**Look for:** parameters that control random generation ranges, array sizes that feed into modulus or indexing operations, any value that is multiplied, divided, or used as a bound and whose effect cascades through multiple function layers. Trace the value from the call site through each function until it reaches its operational use.

### Data format assumptions

Code that produces or consumes structured data (files, serialized objects, notebook cells) may make implicit assumptions about the format that are correct for the current tooling but fragile.

**Prompt:** "This data is stored as [format]. If it's read by [tool], does the tool expect [specific structure], or will it silently produce wrong results?"

**Look for:** serialized data structures where element boundaries matter (e.g., newline-terminated lines vs. single strings), API contracts where field names or types changed between versions, any code that constructs data for consumption by another system without verifying the consumer's expectations.

## Protocol

1. Read the code files first. Do not rely on plans, comments, or variable names.
2. Ask 2-3 questions per round, mixing categories. Include at least one question from data ownership, parameter propagation, or model-fidelity in the first round.
3. Wait for answers before generating follow-ups.
4. If a confusion arises, articulate what assumption led to the confusion and whether that assumption was reasonable.
5. After 3-4 rounds, summarize: confirmed behaviors, bugs found, design decisions, and points that remain unclear.
6. Before implementing modifications, trace at least one complete data flow from a call site through all intermediate functions to its operational use. This catches parameter-propagation bugs that look correct at each individual call.

## Additional prompt

- "Is there a simpler computational path that produces the same result? Conversely, is there a more efficient path that the current code isn't using?"
