# BOSMAX Cowork Agent Orchestration Contract
# Version: v1
# Authority: BOSMAX Systems Architecture
# Status: ACTIVE — docs-only contract
# Last updated: 2026-06-08

---

## 1. AGENT NATURE — DEFINITIVE STATEMENT

BOSMAX agents are **Claude Code prompt-level skill personas**.

They are NOT:
- Autonomous runtime processes
- Deployed agents or containers
- Background execution systems
- Self-triggering or self-scheduling services
- Notion automation layers

They ARE:
- `.md` instruction files stored in `.claude/skills/`
- Loaded and executed by Claude within a human-initiated Claude Code session
- Activated by the BOSMAX orchestrator appointing them to a task
- Session-scoped: they operate for the duration of one Claude Code session and do not persist state independently between sessions

**Implication for operators:** A BOSMAX session requires a human to open Claude Code, present a requirement, and interact with the system. There is no background process running without a human present.

---

## 2. SYSTEM ROLES — THREE DISTINCT LAYERS

```
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1: NOTION                                                     │
│  Role: Raw seed library and reference UI — DOWNSTREAM ONLY           │
│  Stores: Raw creative seeds, product references, copy references,    │
│          avatar references, template references                      │
│  Does NOT store: Final prompts, final approved outputs, QA results   │
│  Does NOT do: Generate prompts, audit quality, expand seeds,         │
│               enforce SOP, route requests                            │
│  Authority level: INPUT ONLY — never upstream truth                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 2: CLAUDE COWORK BOSMAX AGENTS                                │
│  Role: Process / polish / enforce / audit / return final prompt      │
│  Receives: Raw seed from Notion OR unstructured user requirement      │
│  Does: Analyse intent, route to specialist skill, expand and         │
│        enforce SOP/guardrails, audit output, return final prompt     │
│  Authority level: SYSTEM TRUTH — orchestrator is canonical           │
│  Orchestrator file: `.claude/CLAUDE.md` (BOSMAX v11.6)              │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 3: IMAGE / VIDEO GENERATORS                                   │
│  Role: Render only                                                   │
│  Receives: Final deployment-ready prompt from Layer 2                │
│  Does: Render the image or video as instructed                       │
│  Does NOT do: Generate creative concepts, audit quality,             │
│               expand briefs, enforce brand rules                     │
│  Authority level: EXECUTION ONLY — not creative decision-maker       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. CORRECT ARCHITECTURE — FULL FLOW

```
INPUT
  ├─ Notion raw seed (operator retrieves from Notion Seed Library)
  └─ User unstructured requirement (operator types directly into session)
        ↓
BOSMAX Orchestrator (.claude/CLAUDE.md)
  ├─ VISUAL INTAKE GATE (if image/video uploaded — runs before PRE-FLIGHT)
  ├─ PRE-FLIGHT PROTOCOL
  │    ├─ STEP 0: Product Intelligence Lookup (bosmax-product-intelligence)
  │    ├─ STEP 0.5: Market Angle Intelligence (bosmax-market-angle-intelligence)
  │    │            [OPT-IN ONLY — after STEP 0; emits angle_intelligence_pack;
  │    │             no final creative; source-gated competitor research]
  │    ├─ STEP 1: Extract Requirements
  │    ├─ STEP 2: Validate All Fields
  │    ├─ STEP 3: Multi-Block Protocol (if duration > engine max)
  │    ├─ STEP 4: Implicit Requirement Detection
  │    └─ STEP 5: Issue Work Order
  ├─ STORYBOARD GATE (video requests only — before skill dispatch)
  │
  ├─ ROUTE A: IMAGE
  │    bosmax-subject-dna → bosmax-scene-engine
  │    (+ bosmax-commercial-poster-director for poster requests)
  │
  ├─ ROUTE B: VIDEO from brief
  │    bosmax-script-generator
  │
  ├─ ROUTE C: VIDEO from existing image
  │    bosmax-mode-c-executor
  │    (requires source_image_handoff from Route A)
  │
  ├─ ROUTE D: ANALYSIS / REVERSE ENGINEERING
  │    bosmax-image-analyst → then Route A
  │    bosmax-video-analyst → then Route B
  │
  ├─ ROUTE REG: PRODUCT REGISTRATION
  │    bosmax-product-registration
  │
  └─ ROUTE BULK: BULK CONTENT GENERATION
       bosmax-bulk-generator
             ↓
     bosmax-compliance-gate
     (VERIFICATION PASSED or ABORT)
             ↓
     bosmax-final-output-agent
     (.claude/skills/bosmax-final-output-agent.md — prompt-level persona, NOT autonomous runtime)
     (formats clean final delivery; suppresses internal metadata; handles ABORT surface)
             ↓
     USER (operator receives final copy-paste prompt)
             ↓
     IMAGE / VIDEO GENERATOR (renders from final prompt)
```

---

## 4. TERMINAL STATES

Every BOSMAX session resolves to one of three terminal states:

| State | Meaning | Operator action |
|-------|---------|-----------------|
| `VERIFICATION PASSED` | Compliance gate approved output; final prompt is ready for copy-paste to generator | Copy prompt to generator. Session complete. |
| `ABORT` | A hard block was triggered; output is suppressed; reason is declared | Read abort reason. Resolve the stated issue. Restart or continue session. |
| `NEEDS USER CLARIFICATION` | Orchestrator detected missing input it cannot resolve; single targeted question issued | Answer the question. Session resumes. |

No partial outputs are delivered to the user. The system is fail-closed: if the compliance gate does not pass, no prompt leaves the system.

---

## 5. NOTION BOUNDARY — ABSOLUTE RULES

```
BOSMAX AGENTS MAY:
  ✅ Read a raw seed the operator copies from Notion into the session
  ✅ Reference product/copy/avatar data the operator pastes from Notion
  ✅ Produce a final prompt the operator will manually copy to Notion for reference

BOSMAX AGENTS MUST NOT:
  ❌ Write directly to Notion
  ❌ Treat Notion as the source of truth for product data (products/*.yaml is truth)
  ❌ Store final prompts in Notion as system-generated authoritative output
  ❌ Trigger any Notion automation
  ❌ Treat Notion template fields as SOP authority (CLAUDE.md and skills/ are SOP authority)
```

Notion is the operator's scratchpad and reference UI. The BOSMAX repo (`products/*.yaml`, `.claude/skills/`, `.claude/CLAUDE.md`, `registries/`) is the system truth.

---

## 6. NON-SCOPE — WHAT THIS SYSTEM DOES NOT DO

```
OUT OF SCOPE FOR BOSMAX COWORK AGENTS:
  ❌ Autonomous agent execution (no process runs without human in the loop)
  ❌ Background scheduling or cron-triggered content generation
  ❌ Direct Notion read/write
  ❌ Direct posting to TikTok, Instagram, or any social platform
  ❌ Product listing creation (TikTok Shop listing management is separate)
  ❌ Media rendering (generators render; BOSMAX only produces the prompt)
  ❌ Financial decisions, pricing, or campaign budgets
```

---

## 7. VERSIONING AND CHANGE AUTHORITY

This contract reflects BOSMAX v11.6 architecture. Any change to:
- The orchestrator role (CLAUDE.md)
- The skill file inventory (`.claude/skills/`)
- The route definitions (A/B/C/D/REG/BULK)
- The terminal state definitions
- The Notion boundary rules

...requires a PR to this file with updated version number and changelog entry.

**Do not treat verbal session instructions or Notion notes as overrides to this contract.**

---

## 8. RELATED CONTRACT FILES

| File | Purpose |
|------|---------|
| `docs/agents/BOSMAX_AGENT_ROLE_INVENTORY_v1.md` | Full inventory of all 13 units with per-role detail |
| `docs/agents/BOSMAX_RAW_SEED_TO_FINAL_PROMPT_FLOW_v1.md` | End-to-end flow from raw seed to generator render |
| `docs/agents/BOSMAX_FINAL_OUTPUT_HANDOFF_CONTRACT_v1.md` | Final output formatting and delivery rules |
| `docs/agents/BOSMAX_RAW_SEED_TEAM_CONTRACT_v1.md` | Future Raw Prompt Seed Team contract |
| `docs/agents/BOSMAX_MARKET_ANGLE_INTELLIGENCE_CONTRACT_v1.md` | Unit 16 — opt-in PRE-FLIGHT STEP 0.5 angle intelligence layer |
| `registries/angle_intelligence_pack.schema.yaml` | angle_intelligence_pack output schema (Unit 16) |
| `.claude/CLAUDE.md` | Canonical orchestrator — BOSMAX v11.6 |
| `.claude/rules/cowork-operating-map.md` | Pipeline sequences and skill file registry |
| `.claude/rules/video-output-enforcement.md` | Pre-output enforcement checklist for video |
