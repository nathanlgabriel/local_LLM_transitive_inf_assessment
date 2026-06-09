# Local LLM Transitive Inference Assessment

## What this is

An informal comparison of how a handful of locally-runnable LLMs handle a real coding task on an existing research codebase. I gave each model the same task: read a chapter of my dissertation and modify existing code implementing the chapter's model of a reinforcment learning dynamic for a transitive inference task. There were two main modifications I wanted made, (1) to generalize the code from a 5 element transitive inference task to work for an arbitrary number of elements, and (2) to generalize how items in the stimulus set were rewarded so that I could do more than simply reinforce a linear ordering. As I got into the weeds, I ended up giving the models instructions to do more detailed code specific things such as writing a helper function to implement a circular set of rewards rather than the linear ordering, track per-pair statistics, and rewrite the multiprocessing in `concurrent.futures` style. The starting codebase the LLMs received is in [`clean_copy/`](./clean_copy/). Note, also, that this folder did contain a modification_plan.md that I created with Opus 4.7 after explaining the basic changes that I wanted to make to the code. Each model's attempt is in its own folder, listed in the [Runs](#runs) section.

I previously thought Qwen 3.6 would outperform Gemma 4 on this kind of task, based on an [earlier test of the models' abilities to map code to a paper](https://github.com/nathanlgabriel/paper_code_mapping_assessment). Gemma 4 surprised me here by significantly outperforming Qwen, which is why I put together this repo. One clutch thing to note on running 31B with a long context (128k) on 32GB of VRAM is to the flag `--ctx-checkpoints 2` to keep things a manageable size; without it, I'd get crashes on 96k context sizes even though I could load everything in VRAM at the begining of a coding session.

## Key takeaways

- **Gemma 4 31B QAT was the only local model that produced working end-to-end code I'd be willing to run on real data with minor edits.** Both attempts of it worked; the second attempt (with the revised prompt) added the held-out test set, generalization to arbitrary N, the circular variant, and the distance-effect analysis cell.
- **Reasoning-loop stalls hit both 26b a4b and 12b Gemma models.** I'd expected this to be a MoE issue, so seeing 12B (dense) get stuck partway through was a surprise. The MoE 26B A4B also stopped mid-run multiple times and had to be prompted to continue.
- **Grill-me time did NOT track output thoroughness.** Qwen 3.6 27B asked the most questions (21 requiring long written answers) before starting (3–5 hours of back-and-forth) and still significantly underperformed Gemma 4 31B which spent much less time asking questions.
- **The Qwen models took initiative, for better and worse.** Sometimes useful — e.g. adding a floor on a noise-annealing parameter I hadn't asked for. Sometimes annoying — substantially rewriting `modification_plan.md` without being asked.
- **PDF handling diverged.** Qwen 3.6 read the paper PDF directly. The Gemma 4 models initially wrote a Python script to convert it to text first. After I updated llama.cpp (needed for the 12B), one of the later Gemma 4 runs could read the PDF and one still couldn't — llama.cpp's Gemma 4 support seems still in flux.

## Results

The table below summarizes what each run got working and what it didn't. Grades are integer scores from 0–10, awarded by Claude Opus 4.7 (the same model that produced the reference implementation in [`claude/`](./claude/)), based on what the deliverables actually do when run.

| Run | Backend imports | Backend executes | Notebooks parse | Notebooks run | Generalizes to n≠5 | Distance-effect cell | **Grade** |
|---|---|---|---|---|---|---|---|
| **Claude Opus 4.7** (reference, hosted) | ✓ | ✓ | ✓ | 4/4 | ✓ | ✓ | **8** |
| **Gemma 4 31B QAT** (revised prompt) | ✓ | ✓ | ✓ | BASE 4/4; ORIGINAL all but final cell | ✓ | ✓ | **8** |
| **Gemma 4 31B QAT** (original prompt) | ✓ | ✓ (limited scope) | ✓ | 4/4 | ✗ | ✗ | **7** |
| **Gemma 4 31B → 26B A4B** (non-QAT, mid-run switch) | ✓ | ✓ (limited scope) | 2/4 | 2/4 | ✗ | ✓ (where shipped) | **6** |
| **Qwen 3.6 27B** | ✓ | ✗ | ✗ (cell-source bug) | ✗ | ✓ | ✓ in source | **3** |
| **Qwen 3.6 35B A3B** | ✗ (IndentationError) | n/a | ✗ | ✗ | partial | ✓ in source | **2** |
| **Gemma 4 26B A4B QAT** (no `/init`, original prompt) | imports, call fails | ✗ | ✗ (cell-source bug) | ✗ | ✗ | ✗ | **1** |
| **Gemma 4 26B A4B QAT** (with `/init`, revised prompt) | ✓ | ✗ (arity bug) | ✓ | ✗ | ✗ | stub with fake hardcoded prints | **1** |
| **Gemma 4 12B QAT** (revised prompt) | ✓ | ✗ | n/a (.ipynb files weren't valid JSON) | ✗ | ✗ | ✗ | **0** |

The clearest within-model contrast available here is the two Gemma 4 31B QAT runs, which differ only in prompt version and llama.cpp version — the second run is meaningfully more complete.

## This is not a scientific benchmark

A few things to be upfront about before drawing conclusions:

- **N=1 per model.** Single runs, not averaged trials.
- **Not all models received the same prompt or the same amount of grill-me time.** The Qwen 3.6 runs and the non-QAT Gemma runs used an earlier prompt that's not in this repo. After the first Gemma 4 31B QAT run skipped the distance-effect analysis, I explicitly mentioned that kind of analysis during the grill-me phase with the 26B A4B QAT — different verbal instructions before the model started. See the [Confounds](#confounds) table.
- **The original code is messy.** I wrote it without coauthors and there aren't comments aimed at explaining things to a reader. That made the task harder for the models than a well-documented codebase would.
- **Grading is by Claude Opus 4.7.** A frontier hosted model assessing local-model output is the easiest way to get consistent feedback across nine runs, but it has the obvious self-comparison concern: the reference implementation in [`claude/`](./claude/) was also produced by Opus 4.7, and the grader is rating other models against work it has direct knowledge of. The grades should be read as "consistent across runs" rather than "neutral."

## The task

The modifications asked of each model:

- Generalize the existing 5-stimulus transitive-inference simulation to N stimuli (tested at N=7).
- Hold out an interior test pair (canonical `[1, 3]` / `[3, 1]` for the linear case) and report transfer performance on it.
- Add a circular variant where stimuli are arranged in a ring and reward is determined by mod-N distance.
- Track per-pair statistics during the test phase for symbolic-distance-effect analysis.
- Rewrite the multiprocessing using `concurrent.futures.ProcessPoolExecutor` with `SeedSequence`-based per-run RNGs.
- Apply all the above to both the "magnitudes" back-end and the "base/singleside" back-end, and update the four notebooks that consume them.

## Runs

All Gemma 4 runs after the first one used the QAT (quantization-aware-training) variants. The first Gemma 4 run started on the non-QAT 31B and switched to the non-QAT 26B A4B partway through after the 31B crashed.

| Run | Folder | Prompt | Chat log |
|---|---|---|---|
| Claude Opus 4.7 (reference) | [`claude/`](./claude/) | — | — |
| Qwen 3.6 27B | [`transitive_inf_oc_qwen27B/`](./transitive_inf_oc_qwen27B/) | earlier (not in repo) | [session-ses_18e1.md](./transitive_inf_oc_qwen27B/session-ses_18e1.md) |
| Qwen 3.6 35B A3B | [`transitive_inf_qwen36_35v_a3b/`](./transitive_inf_qwen36_35v_a3b/) | earlier (not in repo) | not exported |
| Gemma 4 31B + 26B A4B (non-QAT, mid-run switch) | [`trans_inf_oc_g31_and_26after31crash/`](./trans_inf_oc_g31_and_26after31crash/) | earlier (not in repo) | not exported |
| Gemma 4 31B QAT (1st run) | [`trans_inf_oc_g31qat/`](./trans_inf_oc_g31qat/) | [`concurrent_futures_full_prompt.txt`](./concurrent_futures_full_prompt.txt) | not exported |
| Gemma 4 26B A4B QAT (no `/init`) | [`trans_inf_oc_g26b_a4b_qat_forgot_init/`](./trans_inf_oc_g26b_a4b_qat_forgot_init/) | [`concurrent_futures_full_prompt.txt`](./concurrent_futures_full_prompt.txt) | [session-ses_156e.md](./trans_inf_oc_g26b_a4b_qat_forgot_init/session-ses_156e.md) |
| Gemma 4 12B QAT | [`trans_inf_oc_g12b_qat/`](./trans_inf_oc_g12b_qat/) | [`concurrent_futures_full_prompt_revised.txt`](./concurrent_futures_full_prompt_revised.txt) | [session-ses_1568.md](./trans_inf_oc_g12b_qat/session-ses_1568.md) |
| Gemma 4 26B A4B QAT (with `/init`) | [`trans_inf_oc_g26b_a4b_qat_with_init/`](./trans_inf_oc_g26b_a4b_qat_with_init/) | [`concurrent_futures_full_prompt_revised.txt`](./concurrent_futures_full_prompt_revised.txt) | [session-ses_1562.md](./trans_inf_oc_g26b_a4b_qat_with_init/session-ses_1562.md) |
| Gemma 4 31B QAT (2nd run, revised prompt) | [`trans_inf_oc_g31qat_new_prompt/`](./trans_inf_oc_g31qat_new_prompt/) | [`concurrent_futures_full_prompt_revised.txt`](./concurrent_futures_full_prompt_revised.txt) | [session-ses_1560.md](./trans_inf_oc_g31qat_new_prompt/session-ses_1560.md) |

A few per-run notes worth flagging:

- **Gemma 4 31B QAT (1st run).** One notebook filename was emitted with opencode tool-call syntax leaking into the path mid-generation — the literal string `structure_noiseAnn_dsktp_2s_BASElearning-MV10_mod.ipynb}<tool_call|> Barack Obama once said "Hope" is not a strategy, but I have a strategy. I will now create the remaining two notebooks. <channel|><|tool_call>call:write{content:"`. Worth noting as a failure mode.
- **Gemma 4 26B A4B QAT (no `/init`).** I forgot to run opencode's `/init` for this session, which may have contributed to the quality drop. Also the first run where I explicitly mentioned distance-effect analysis during grill-me, because the 31B QAT had skipped it.
- **Gemma 4 12B QAT.** The `.ipynb` files from this run may have been corrupted — GitHub refused to accept them on upload. Only the chat log is in the folder.
- **Gemma 4 31B QAT (2nd run).** Re-run for two reasons: I'd forgotten to export the chat log the first time, and I wanted to check whether the revised prompt was too convoluted for the smaller models. The 12B and 26B A4B both struggled with the revised prompt more than I expected, and a re-run of the model that handled the original prompt best was the cleanest way to test that.

## Confounds

| Run | Prompt | Grill-me time | `/init`? | llama.cpp version |
|---|---|---|---|---|
| Qwen 3.6 27B | earlier (not in repo) | 3–5 hrs | yes | older |
| Qwen 3.6 35B A3B | earlier (not in repo) | not noted | yes | older |
| Gemma 4 31B + 26B A4B (non-QAT) | earlier (not in repo) | not noted | yes | older |
| Gemma 4 31B QAT (1st) | original | ~30 min | yes | older |
| Gemma 4 26B A4B QAT (no init) | original | ~1 hr (with explicit distance hint) | **no** | older |
| Gemma 4 12B QAT | revised | not noted | yes | updated |
| Gemma 4 26B A4B QAT (with init) | revised | not noted | yes | updated |
| Gemma 4 31B QAT (2nd) | revised | not noted | yes | updated |

The cleanest within-model comparison available here is the two 31B QAT runs — same model, same flags, different prompt version and llama.cpp version.

## Prompts

- [`concurrent_futures_full_prompt.txt`](./concurrent_futures_full_prompt.txt) — first 31B QAT run and first 26B A4B QAT run (no `/init`).
- [`concurrent_futures_full_prompt_revised.txt`](./concurrent_futures_full_prompt_revised.txt) — 12B QAT, second 26B A4B QAT (with `/init`), and second 31B QAT.

The earlier Qwen and non-QAT Gemma runs used a prompt that predates both of the above and isn't in this repo.

## Appendix: llama.cpp flags

Each run was served with `llama-server` using the exact command below. Models were driven through [opencode](https://github.com/anomalyco/opencode).

**Qwen 3.6 27B**

```bash
./llama-server -hf unsloth/Qwen3.6-27B-GGUF:Q4_K_M -ngl 99 \
  --split-mode layer --tensor-split 1,1.04 --flash-attn on \
  --ctx-size 200000 --parallel 1 --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 20 --top-p 0.95 --threads 6 \
  --host 0.0.0.0 --port 8080 --jinja \
  --chat-template-kwargs '{"preserve_thinking": true}' --alias local-model
```

**Qwen 3.6 35B A3B**

```bash
./llama-server -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.12 --flash-attn on \
  --ctx-size 256000 --parallel 1 --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 20 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja \
  --chat-template-kwargs '{"preserve_thinking": true}' --alias local-model
```

**Gemma 4 31B (non-QAT)**

```bash
./llama-server -hf unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.04 --flash-attn on \
  --ctx-size 128000 --parallel 1 --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 64 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja --alias local-model
```

**Gemma 4 26B A4B (non-QAT)**

```bash
./llama-server -hf unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.04 --flash-attn on \
  --ctx-size 256000 --parallel 1 --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 64 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja --alias local-model
```

**Gemma 4 31B QAT** (both runs)

```bash
./llama-server -hf unsloth/gemma-4-31B-it-qat-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.08 --flash-attn on \
  --ctx-size 128000 --ctx-checkpoints 2 --parallel 1 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 64 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja \
  --chat-template-kwargs '{"preserve_thinking": true}' --alias local-model
```

**Gemma 4 26B A4B QAT** (both runs)

```bash
./llama-server -hf unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.08 --flash-attn on \
  --ctx-size 256000 --ctx-checkpoints 2 --parallel 1 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --temp 1.0 --top-k 64 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja \
  --chat-template-kwargs '{"preserve_thinking": true}' --alias local-model
```

**Gemma 4 12B QAT**

```bash
./llama-server -hf unsloth/gemma-4-12B-it-qat-GGUF:UD-Q4_K_XL -ngl 99 \
  --split-mode layer --tensor-split 1,1.08 --flash-attn on \
  --ctx-size 256000 --ctx-checkpoints 2 --parallel 1 \
  --temp 1.0 --top-k 64 --top-p 0.95 --threads 16 \
  --host 0.0.0.0 --port 8080 --jinja \
  --chat-template-kwargs '{"preserve_thinking": true}' --alias local-model
```
