# Implementation Plan — Live Match Intelligence Desk

Companion to `ai/docs/SPEC-V1.md` and `ai/knowledge/AGENT.md`. This breaks the build into
ordered, manageable steps. Each step lists **what to build**, **why it's here**, and a
**done when** acceptance check. Build window ≈ 2026-10-20 → 2026-10-27; submit 2026-10-27.

Guiding rules (from the spec): code does deterministic logic, LLMs only produce language;
nothing publishes unverified; everything carries provenance (fact IDs + verdict). Build
local-first with a mock LLM, swap in Foundry late.

---

## Phase 0 — Project scaffold (½ day)

**What**
- Lay out the package under `src/` (e.g. `src/mid/` — "match intelligence desk"):
  `models/`, `ingest/`, `stats/`, `producer/`, `agents/`, `critic/`, `publisher/`, `web/`,
  `pipeline/`, `generator/`.
- Add dev tooling via uv: `pytest`, `ruff`, `pydantic`, a web framework (`fastapi` + `uvicorn`),
  `httpx`. Wire `uv run pytest` and `uv run ruff check`.
- Add `src/mid/config.py` (env-driven: mock-vs-Foundry flag, thresholds, cooldowns, paths).
- Make `main.py` a thin CLI: `generate`, `replay`, `serve`.

**Why** A clean seam between stages and config-driven thresholds is the enterprise-controls story.

**Done when** `uv run pytest` runs (even with 0 tests), `ruff` is clean, `main.py --help` lists the subcommands.

---

## Phase 1 — Data model + synthetic generator + schema (1 day)

**What**
- Define `Event`, `Fact`, `NarrativeItem` as pydantic models (shapes in SPEC-V1 §Data model).
  Add enums for `event.type`, `outcome`, `audience`, `status`.
- Build `generator/` producing a single realistic synthetic match: a sequence of events with
  plausible coordinates, timing, players, teams, and related-event links. Seedable (`--seed`).
- Persist a match as JSON lines; document the schema in `ai/docs/` or a docstring.

**Why** Rule 4.7 requires synthetic football-realistic data; a seeded generator is our fallback
and makes everything downstream reproducible.

**Done when** `uv run python -m mid generate --seed 1` writes a match file that round-trips
through the pydantic models with no validation errors, and two runs with the same seed are identical.

---

## Phase 2 — Ingest + MatchState + Replayer (1 day)

**What**
- `ingest/`: validate schema, drop/flag duplicates, enforce monotonic time, check physical
  plausibility (coords in bounds, speeds sane), apply safe corrections. Rejections → `quality_log`
  with reason codes.
- `pipeline/state.py`: `MatchState` — the shared object all stages read/write (events-so-far,
  facts, narrative items, quality_log, running tallies). Single source of truth.
- `replayer/`: emit ingested events as a **timed stream** (wall-clock-scaled match clock) onto an
  in-process async queue. Include a `--speed` multiplier for demos/tests.
- Seed the **fault fixture**: a small event file with known faults + an expected-rejections file.

**Why** Shared MatchState is the multi-agent "shared-state coordination" evidence; the quality_log
is the data-quality evidence.

**Done when** replaying the fault fixture produces exactly the expected rejections, and a clean
match streams end-to-end into MatchState in order.

---

## Phase 3 — Stats / Interpret (1 day)

**What**
- `stats/`: deterministic calculators — pass distance/completion/difficulty, shot speed,
  possession share, pressure, tempo. Each emits **Facts** carrying `source_event_ids`.
- Facts accumulate into MatchState as events arrive.

**Why** This is the "Interpret" stage and the factual ground truth the Critic will verify against.
LLMs must never compute these.

**Done when** unit tests assert each calculator against **hand-computed values** on a tiny fixture;
every Fact traces back to the event IDs it came from.

---

## Phase 4 — Producer (½ day)

**What**
- `producer/`: rules that score each moment's narration-worthiness, apply **cooldowns** (avoid
  spamming similar lines), and log *why* a moment was chosen or skipped. Emits a `NarrationRequest`
  (the moment + the relevant Fact IDs) — and nothing else goes to the Narrator.

**Why** Keeps moment selection deterministic and explainable; the Narrator's input is tightly scoped
so it can't wander.

**Done when** a test on a fixed event sequence yields the expected chosen moments and skip reasons.

---

## Phase 5 — Agent interface + mock LLM (½ day)

**What**
- `agents/base.py`: a small agent contract (typed request → structured JSON response) used by
  Narrator, Critic, Personalizer, Localizer. Make handoffs explicit and loggable (A2A/MCP-style).
- `agents/llm.py`: an LLM client behind an interface with a **mock implementation** (deterministic,
  canned/structured responses) selected by config. Foundry client stubbed for later.

**Why** Local-first development; the explicit contract is the multi-agent "distinct roles + handoffs"
evidence and makes everything testable without network/cost.

**Done when** the mock LLM returns valid structured JSON for each agent type and the pipeline can call it.

---

## Phase 6 — Narrator + Critic + recovery (1.5 days) ← core value

**What**
- `agents/narrator.py` (LLM): input is the `NarrationRequest` only; outputs a structured line
  that **cites fact IDs**; low temperature.
- `critic/` (rules + LLM): **deterministic checks first** — numbers, names, and fact IDs must match
  the Facts; **then** an LLM check for unsupported paraphrased claims. Verdict
  `approved | rejected | fallback`.
- **Recovery:** on `rejected`, retry once feeding back the Critic's reason; if it fails again, or on
  any LLM error/timeout, emit a **template fallback** line marked `degraded`.

**Why** This is the whole differentiator: nothing unverified reaches the feed, and the feed never
dies on stage. It's the Explainability + Multi-Agent recovery evidence.

**Done when** Critic tests pass on good items (approved) and bad items (wrong number/name/
unsupported claim → rejected), and a forced LLM failure yields a degraded fallback line.

---

## Phase 7 — Personalizer + Localizer (1 day)

**What**
- `agents/personalizer.py` (LLM): from the **approved analyst line + the same Facts**, produce a
  casual **Fan** rendering — plainer, explains *why it matters*, **no new numbers**. Critic
  re-verifies the Fan line against the same Facts.
- `agents/localizer.py` (LLM): Spanish from approved text + the same Facts; numbers and names must
  match. Add a `glossary` mapping player names and club nicknames to canonical forms.

**Why** "Personalize" is the mandated 5th stage and the Grand Prize's personalization/accessibility
evidence; verified multilingual output is the differentiator over hallucinating commentary.

**Done when** for a sample moment the pipeline produces 4 verified variants
(Analyst/Fan × EN/ES), all passing the Critic, numbers/names consistent across all four.

**Cut line:** if time-pressed, ship ES before Fan mode (ordering per SPEC-V1).

---

## Phase 8 — Publisher + web panel (1.5 days)

**What**
- `publisher/`: push approved items to clients over SSE/WebSocket.
- `web/`: broadcast-style panel —
  - main feed with **Analyst/Fan** toggle and **EN/ES** toggle;
  - live **stats side panel**;
  - **trace view** showing each stage's input/output and handoffs;
  - each line shows its cited facts + Critic verdict; `degraded` items marked;
  - a **quality_log counter** of faults caught;
  - accessible: keyboard nav, contrast, readable at distance.

**Why** Render stage + the full 20% UX/Presentation criterion; the trace view is the multi-agent
money shot for the demo.

**Done when** running `serve` and replaying a match shows lines appearing live, toggles work, and
the trace view reflects real per-stage handoffs.

---

## Phase 9 — End-to-end + test hardening (½ day)

**What**
- A seeded **end-to-end replay snapshot** test: generator → … → published items, asserted stable.
- Fill test gaps: Ingest faults, Stats values, Producer selection, Critic verdicts across
  audience/language variants.
- Run `ruff` + `pytest` green.

**Done when** `uv run pytest` is green and the e2e snapshot is deterministic across runs.

---

## Phase 10 — Azure deployment (1 day)

**What**
- Swap mock LLM → **Microsoft Foundry** deployment via config (no code path change).
- Orchestrate the four agents with **Microsoft Agent Framework**; use **Azure MCP** where it
  strengthens the agent/tool contract.
- Storage: Cosmos DB or Azure SQL (pick one — see Open Questions). Transport: Event Hubs optional.
- Containerize; deploy to **Azure Container Apps**. Wire **Application Insights** for traces.
- Keep provenance (fact IDs + verdict), quality_log, and trace retained — the enterprise story.

**Why** Foundry/Agent Framework/Container Apps/Azure data are the hero techs and the Foundry +
Azure Cloud Native + Enterprise category evidence. The deployed URL is the **required live test link**.

**Done when** the app runs on Container Apps with Foundry generating lines, the public URL works,
and App Insights shows per-stage telemetry.

---

## Phase 11 — Submission package (½ day)

**What** (rule 4.4 — all required)
- Public GitHub repo (confirm visibility).
- **Demo video under 2 minutes** on YouTube/Vimeo/Facebook/Youku — lead with the trace view and the
  verified Analyst/Fan × EN/ES feed.
- Written pitch: what it is, the problem it solves, and the **Microsoft/Azure tech used** (Foundry,
  Agent Framework, Azure MCP, Container Apps, Cosmos/SQL, App Insights, Event Hubs).
- **Live test link** public/free/working through **2026-11-10**; include creds if gated.
- Map the submission explicitly to the five stages and the target categories.

**Done when** all four artifacts exist, links are public, and a fresh browser can run the demo.

---

## Dependency order (critical path)

```
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11
                         └ 8 (panel) can start against mock once 6 lands
```

Phases 1–9 are fully local (mock LLM); Azure (10) is a late swap. If the week slips, the demo can be
given from a local `serve` — but the **live link is a hard submission requirement**, so protect Phase 10.

## Open questions to resolve early
- Verified synthetic dataset, or commit to the generator? (affects Phase 1)
- Cosmos DB vs. Azure SQL? (affects Phase 10)
- Which Foundry model? Pin it in SPEC-V1 + AGENT.md once chosen.
- Is a mock-LLM local build acceptable as the demo fallback if Foundry quota is tight?
