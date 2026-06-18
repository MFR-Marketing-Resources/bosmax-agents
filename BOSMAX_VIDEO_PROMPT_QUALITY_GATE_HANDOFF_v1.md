# BOSMAX Video Prompt Quality Gate — Cross-Agent Handoff (v1)

- **Status:** LIVE on `master` (PR #63 + PR #64, merged 2026-06-18)
- **Audience:** every agent that authors or compiles BOSMAX video prompts — Claude Code, Codex, ChatGPT, Gemini, Hermes, and any human operator.
- **Canonical authority:** `.claude/CLAUDE.md` (orchestrator) wins on any conflict. This file is a quality contract + alert, not a second orchestrator.

---

## Why this exists (read before mass generation)

We are about to mass-generate video + poster templates into Notion. Four
recurring prompt-quality defects have wasted real firefighting time. They are
now **deterministically blocked** at the compiler AND on the raw prompt text.
Any prompt that re-introduces them must be treated as a hard failure, not a
style nit. **Do not push a video prompt to Notion until it clears the gate.**

There are two lanes that can emit a video prompt:

1. **Deterministic compiler** — `scripts/video_prompt_compiler.py`
   (`video_template_compiler_runtime`). Already enforces all four gates on
   structured YAML templates. **Prefer this lane for mass generation.**
2. **Chat-lane LLM** — any agent following `.claude/skills/bosmax-script-generator.md`.
   This lane bypasses the compiler, so its output must be checked by the
   text gate below.

---

## The 4 non-negotiable rules

### A. NO internal metadata in the prompt body
The engine-facing prompt must contain only what the video engine should read.
Orchestration / budget scaffolding is forbidden inside the prompt text.

- ❌ WRONG: `This is SET 1 of a two-prompt 16-second multi-prompt sequence. Runtime plan is [10,6]. Do not compile as one 16-second video. Do not use two equal 8-second blocks. output_mode=MULTI_PROMPT_SET. block_source=...`
- ✅ RIGHT: `Build a complete 10-second GROK commercial video for TikTok Shop Malaysia, covering the hook and pain beat of a continuous two-part video. Render only this beat.`
- Set framing (`SET 1 / SET 2`, runtime plan, block math) lives in the **outer header** the operator reads — never inside Section 1–9 text.
- Forbidden tokens (non-exhaustive): `output_mode=`, `block_source=`, `dialogue_word_count=`, `safe_max_words=`, `pace_class=`, `Runtime plan`, `Do not compile as one`, `Do not use two equal`, `multi-prompt sequence`.

### B. Dialogue must FILL the duration (range to target, never below minimum)
Short dialogue leaves dead air; the engine fills it with hallucinated motion =
glitch. Range the spoken line to the **target**, not the minimum.

- Budget source of truth: `registries/dialogue_budget_corridor.yaml`.
- Quick reference (BM / BRISK_UGC), `minimum → target`:
  | Clip | min | target | safe-max |
  |------|-----|--------|----------|
  | 6s   | 14  | 15–16  | 17 |
  | 8s   | 19  | 20–21  | 22 |
  | 10s  | 24  | 26–28  | 28 |
  | 12s  | 30  | 32–34  | 34 |
  | 15s  | 37  | 40–42  | 42 |
- Below `minimum` = **UNDERFILLED = REWRITE_REQUIRED** (hard block, not a warning).
- Above `safe_max` = overfill = also blocked.

### C. NO English / internal labels code-switched into a BM spoken line
Storyboard handles are internal, not speech.

- ❌ WRONG (spoken): `"Family shelf nampak kemas. Tap tengok harga sekarang."`
- ✅ RIGHT (spoken): `"Rak keluarga nampak kemas. Tap tengok harga sekarang."`
- Blocked tokens inside a BM line: `family shelf`, `shelf cue`, `product hero`, `b-roll`, `visual seed`, `narrative function`, `hook beat`, `cta beat`.

### D. Resolve presenter_route — never silently make a talking video faceless
A speaking video needs a face with synced speech. "Voiceover only" is correct
**only** for an intentionally faceless product-only clip.

- `presenter_route` values: `PRESENTER_FULL` / `PRESENTER_HYBRID` (lip-sync) / `PRODUCT_ONLY_VO` (faceless voiceover).
- **Default for a dialogue video = `PRESENTER_HYBRID`** (lip-sync). Product-only voiceover only on explicit request / a 6s CTA close / a silent montage.
- Section 6 must declare lip-sync (presenter) or honest voiceover (faceless) — never a silent default.
- ❌ WRONG: a 16s talking commercial silently emitted as faceless "Voiceover only".

---

## Block-chain math is AUTO-COMPUTED (both engines) — the operator never specifies the split

The operator supplies only **engine + total duration**. The system resolves the
lane and **computes** the block chain deterministically (`scripts/video_block_plan.py`,
registry `registries/video_engine_duration_contracts.yaml`). Do not ask the user
for a split, and do not hand-write one.

Preview any plan:
```bash
python scripts/video_block_plan.py --engine-id GOOGLE_FLOW --duration 38
```

**Supported single-block (one prompt set):**

| Engine | Durations |
|---|---|
| GROK | 6s, 10s |
| GOOGLE_FLOW | 8s (8s lane), 10s (10s lane) |

**Supported multi-block chains (auto-resolved lane + computed split):**

| Engine | Total | Computed chain | Lane |
|---|---|---|---|
| GROK | 12s | [6,6] | extension |
| GROK | 16s | [10,6] | extension |
| GROK | 18s | [6,6,6] | extension |
| GROK | 20s | [10,10] | extension |
| GROK | 30s | [10,10,10] | extension |
| GOOGLE_FLOW | 16s | [8,8] | 8s (FLOW_EXTEND_UI) |
| GOOGLE_FLOW | 20s | [10,10] | 10s (FLOW_EXTEND_10S) |
| GOOGLE_FLOW | 30s | [10,10,10] | 10s |
| GOOGLE_FLOW | 32s | [8,8,8,8] | 8s |
| GOOGLE_FLOW | 38s | [10,10,10,8] | 10s (single 8s tail) |
| GOOGLE_FLOW | 40s | [10,10,10,10] | 10s |
| GOOGLE_FLOW | 48s | [8,8,8,8,8,8] | 8s |
| GOOGLE_FLOW | 50s | [10,10,10,10,10] | 10s |
| GOOGLE_FLOW | 56s | [8,8,8,8,8,8,8] | 8s |
| GOOGLE_FLOW | 60s | [10,10,10,10,10,10] | 10s |

**How the math works (deterministic, fail-closed):**
- Each engine/lane declares `block_math` (primary block size + optional single
  tail). The greedy solver uses as many primary blocks as possible, then one
  allowed tail. GROK = {primary 10, tail 6}; Flow 8s lane = {primary 8}; Flow
  10s lane = {primary 10, tail 8 ×1}.
- GROK never uses an 8s block; the Flow 10s lane never uses the GROK [10,6]
  split and never down-mixes to 8s; the two Flow lanes never mix in one render.
- A duration the engine **cannot** represent (e.g. GROK 7s, Flow 13s/14s) is
  **rejected** — fail closed, never a silent wrong split.
- To enable a new total, add the number to that lane's
  `valid_total_durations_seconds`; the split is computed automatically (no
  hand-typed block array needed). 38s is the live proof: it is computed, not
  table-listed.

## The deterministic gate (run this on every prompt before Notion)

```bash
# scan a raw prompt text file (whatever the LLM or compiler produced):
python scripts/validate_final_video_prompt_text.py path/to/prompt.txt --language BM --pace BRISK_UGC

# self-test (no argument): the original failing case must BLOCK, a clean prompt must PASS
python scripts/validate_final_video_prompt_text.py
```

- Exit `0` + `✅ CLEAN` → safe to ship.
- Exit `1` + `⛔ BLOCKED` + findings → **do not ship**; rewrite and re-run.
- It scans the raw text for all four defects (A/B/C/D) and imports its pattern
  lists + WPS corridor from the same artefacts the compiler uses (one source of
  truth — no drift).

For structured YAML templates, the compiler validator is the equivalent gate:

```bash
python scripts/validate_video_prompt_compiler.py     # compiler lane
npm run mandor:check                                 # full repo authority gate
```

---

## Mass-generation workflow (Notion) — the firefighting killer

1. Generate each video prompt (prefer the compiler lane; YAML in
   `samples/video_template_compiler/` is the template shape).
2. **Gate every prompt** with `validate_final_video_prompt_text.py` (chat-lane)
   or `validate_video_prompt_compiler.py` (compiler lane).
3. Only `CLEAN` prompts get written to Notion. A blocked prompt is rewritten,
   never waved through.
4. Notion writes still go through the existing governance (Compliance Gate +
   the PR-#51 Notion writer) — this gate is an additional pre-write filter, not
   a replacement.

---

## Where the truth lives (do not duplicate)

| Concern | File |
|---|---|
| Orchestrator / routing / engine rules | `.claude/CLAUDE.md` |
| Compiler lane | `scripts/video_prompt_compiler.py`, doc `docs/video_template_compiler_runtime.md` |
| Raw-text gate (chat-lane net) | `scripts/validate_final_video_prompt_text.py` |
| WPS budget corridor | `registries/dialogue_budget_corridor.yaml` |
| Pre-output enforcement checklist | `.claude/rules/video-output-enforcement.md` |
| Script-generator skill (chat lane) | `.claude/skills/bosmax-script-generator.md` |
| Regression fixture (original bug) | `samples/video_template_compiler/wps_underfill_multi.yaml` |

If a rule here ever conflicts with `.claude/CLAUDE.md`, CLAUDE.md wins — and this
file should be patched to match.
