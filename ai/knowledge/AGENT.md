# AGENT.md — Project Orientation

Read this first. It tells an agent (or a new teammate) what this project is, why it exists,
how it is built, and the constraints that must not be broken. Source of truth for scope and
design is `ai/docs/SPEC-V1.md`; this file is the quick orientation around it.

## What this is

**Live Match Intelligence Desk** — a pipeline that turns a stream of *synthetic* football
(soccer) match events into explainable, verified, personalized commentary, shown on a
broadcast-style web panel. Every line of commentary cites the facts it came from and is
checked by a Critic before it is published, in English and Spanish, for two audiences
(a data-focused analyst and a casual fan).

One-line pitch: *every moment explained, every claim verified, every fan served.*

## Why we are doing it

This is an entry for the **Inside the Game** hackathon (Microsoft × Premier League).

- **Challenge:** turn synthetic football events into explainable match intelligence across a
  five-stage pipeline: **Ingest → Interpret → Explain → Render → Personalize**.
- **Our angle / differentiator:** most "AI commentary" projects hallucinate. Ours cannot
  publish an unverified claim — a deterministic Critic gates every line against the facts.
  On top of that we do verified multilingual output and genuine per-audience personalization,
  which is exactly what the Grand Prize ("accessible and personalized experiences") rewards.

### Prize targets (drives most design decisions)
- **Grand Prize** — primary ambition.
- **Best Multi-Agent System** — primary category: distinct agent roles, shared state,
  explicit handoffs, recovery from failure.
- **Best Use of Microsoft Foundry** — our LLM agents run on Foundry.
- **Best Enterprise Solution** — provenance, transparency, controls, path to adoption.
- **Best Azure Cloud Native Integration** — Azure Container Apps + Azure services.

An entrant can win at most one Grand Prize + one Category Prize, so categories are *evidence
angles*, not separate builds. Judging is five criteria at 20% each: Technological
Implementation, Agentic Design, Real-World Impact, UX & Presentation, Adherence to Category.

## Hard rules — do not violate

- **Synthetic data only.** Rule 4.7 requires synthetic, football-realistic data. **No real
  match data, no video footage.** Use the in-repo generator (or a verified synthetic set).
- **Newly created** after 2026-09-29. Nothing derived from sponsor-funded/licensed work.
- **Deadlines (PT):** registration closed 2026-10-20; **submission due 2026-10-27 23:59**;
  judging runs to **2026-11-10** — the live demo link must stay public, free, and working
  that whole time.
- **Submission needs:** public GitHub repo; demo video **under 2 min** on YouTube/Vimeo/
  Facebook/Youku; written pitch naming the Microsoft/Azure tech used; a live public test link.
- Team size ≤ 4; one Representative submits.

## How it works (architecture)

```
Replayer → Ingest → Stats → Producer → Narrator(LLM) → Critic(rules+LLM)
        → Personalizer(LLM) → Localizer(LLM) → Publisher → Web panel
```

All stages read/write a shared **MatchState**. Split: **code does the logic, LLMs do the
language.** Agents hand off over an explicit contract (A2A-style / MCP) so the trace is legible.

| Stage | Kind | Job |
|-------|------|-----|
| Replayer + Ingest | code | Replay synthetic events as a timed stream; validate, de-dup, correct; bad events → `quality_log` |
| Stats | code | Events → football stats + context; emits **Facts** with `source_event_ids` |
| Producer | code (rules) | Scores moments, cooldowns, logs *why*; emits a `NarrationRequest` |
| Narrator | LLM | Request → structured JSON line citing fact IDs; low temperature |
| Critic | rules + LLM | Deterministic number/name/fact-ID checks, then LLM check for unsupported claims; verdict `approved\|rejected\|fallback` |
| Personalizer | LLM | Approved analyst line + same Facts → casual **Fan** rendering (no new numbers); Critic re-verifies |
| Localizer | LLM | Spanish from approved text + same Facts; numbers/names must match; glossary for names/nicknames |
| Publisher + Panel | code | SSE/WebSocket to a broadcast-style panel with Analyst/Fan + EN/ES toggles, live stats, trace view |

**Recovery:** retry once with the Critic's reason, then template fallback; any LLM error or
timeout → fallback with a `degraded` flag. This is deliberate — it is the "recovery from
failures" evidence for the Multi-Agent category and keeps the feed live on stage.

### Core data shapes
- **Event:** id, match_id, minute, second, type, team, player, x, y, end_x, end_y, outcome,
  period (1|2, optional), card_color (yellow|red, optional), related_event_id, ts
- **Fact:** id, kind (`FactKind`), scope (`FactScope`: home|away|match), value, unit, entity_refs,
  source_event_ids, minute
- **Narrative item:** id, text, lang, audience(analyst|fan), fact_ids, moment_type, priority,
  status(draft|approved|rejected|fallback), degraded

## Tech stack

- **Local/dev:** Python ≥ 3.12, managed with **uv** (`uv run`, `uv add`). Entry: `src/main.py` (→ `mid.cli`).
- **Libraries so far:** pydantic (models), FastAPI + uvicorn (panel), httpx (LLM calls). Microsoft
  Agent Framework and Azure SDKs are not yet added.
- **Agents/orchestration:** Microsoft Agent Framework (Narrator, Critic, Personalizer, Localizer).
- **LLM:** Microsoft Foundry deployment. **Build local first with a mock LLM, then swap in Foundry.**
- **Transport:** in-process queue for local dev; Event Hubs optional in cloud.
- **Storage:** Cosmos DB or Azure SQL.
- **Hosting:** Azure Container Apps (also serves the required public test link).
- **Observability:** Application Insights.
- Prefer the latest Claude / hero technologies where they strengthen a judging criterion
  (Foundry, Agent Framework, Azure MCP).

## Working agreements for agents

- **Code logic is deterministic and tested; LLMs only generate language.** Never let an LLM
  compute a stat or invent a number — it must cite a Fact.
- **Nothing publishes unverified.** If you add an output path, it goes through the Critic.
- Keep stats **unit-tested against hand-computed values**; Ingest has a fixture of known
  faults with expected rejections; Critic tested on good/bad items incl. EN/ES + Analyst/Fan;
  one seeded end-to-end replay snapshot.
- When a decision affects scope or judging, check it against `ai/docs/SPEC-V1.md` and the
  official rules before building.
- Everything published carries provenance (fact IDs + verdict) — don't strip it; it's the
  enterprise/explainability story.

## Repo map (current)

```
pyproject.toml            # uv project "pl-hackathon", py>=3.12; fastapi, httpx, pydantic, uvicorn;
                          # dev: pytest, ruff (line-length 100, rules E,F,I,UP,B); hatchling build -> src/mid
src/main.py               # entry point; delegates to mid.cli.main
src/mid/__main__.py       # `python -m mid`
src/mid/cli.py            # argparse CLI: generate, replay (done), serve (Phase 8)
src/mid/config.py         # frozen Settings loaded from MID_* env vars
src/mid/models/           # Event, Fact, NarrativeItem + enums (the data contract); pitch.py (shared
                          # pitch size + attack_direction)
src/mid/generator/        # synthetic.py (seeded match simulator), storage.py (JSONL read/write)
src/mid/ingest/           # validator.py: dedupe, plausibility filter, time sort (no quality_log yet)
src/mid/stats/            # calculations.py: deterministic calculators -> Facts
src/mid/pipeline/         # match_state.py: MatchState (counters, events, facts, fact_log)
src/mid/replayer/         # replayer.py: ingest + timed stream onto an asyncio queue
src/mid/producer|critic|agents|publisher|web/   # empty stubs (docstring only)
tests/                    # test_generator, test_models, test_scaffold, test_ingest,
                          # test_match_state, test_calculations
ai/docs/SPEC-V1.md        # authoritative spec: scope, stages, plan, risks
ai/knowledge/             # orientation + reference (this file)
```

## Build status vs SPEC-V1 §Plan

Build order: generator/schema/Ingest → Stats/MatchState/Replayer → Producer → Critic → Foundry +
Personalizer + Localizer + panel → Azure deploy → demo/submit.

| Step | State |
|------|-------|
| Scaffold (CLI, config, package layout) | Done |
| Schema (Event, Fact, NarrativeItem) | Done |
| Synthetic generator + JSONL storage | Done |
| Ingest (dedupe, plausibility, time sort) | Partial: no structured `quality_log`, no fault fixture/expected rejections, batch not live |
| MatchState + Replayer | Done (replay CLI works) |
| Stats (possession, pass completion/distance/difficulty, pressure, tempo, shot conversion) | Done; shot speed not implemented (no data for it) |
| Producer, Critic, agents, publisher, web | Not started (stubs) |

Not yet existing: `NarrationRequest`, `quality_log` model. The `serve` CLI subcommand is
registered but returns exit code 1 ("not implemented").

## What exists today

### Scaffold
- **CLI** (`mid.cli`): `mid generate [--seed N] [--match-id ID] [--output PATH]` (default seed 1,
  default output `<MID_DATA_DIR>/match-<seed>.jsonl`) and `mid replay --match-id ID [--input PATH]`.
- **Settings** (`mid.config`): `MID_LLM_BACKEND` (`mock`|`foundry`, default `mock`), `MID_DATA_DIR`
  (`data`), `MID_REPLAY_SPEED` (1.0, must be > 0), `MID_NARRATION_COOLDOWN_MINUTES` (3.0),
  `MID_MAX_NARRATOR_RETRIES` (1). Validated in `__post_init__`. This is the mock→Foundry switch
  and the "config-driven thresholds" enterprise-controls evidence.

### Data contract (`mid.models`) — everything downstream depends on this
- **Enums:** `EventType` (pass, shot, carry, dribble, tackle, interception, clearance, foul, save,
  goal, card), `Outcome` (success, failure, goal, saved, blocked, off_target, neutral),
  `Audience` (analyst|fan), `Status` (draft|approved|rejected|fallback), `CardColor` (yellow|red),
  `FactKind` (possession_share, pass_completion, pass_distance, pass_difficulty, pressure, tempo,
  shot_conversion), `FactScope` (home|away|match).
- **Event:** `extra="forbid"`, `frozen=True`. minute >= 0, second 0..59, non-empty id/match_id/team;
  player, coords, outcome, related_event_id optional. `period` (1|2) drives attack direction;
  when missing (older data) stats fall back to the minute-45 boundary. A card with no `card_color`
  counts as yellow. This is Ingest's first (schema) gate.
- **Fact:** frozen. `scope` says whether it is team (home|away) or match-level (tempo).
  Fact ids are `<kind>-<scope>-<last event id>`, so an id identifies one state. `source_event_ids` has `min_length=1` — a Fact with no source events cannot
  exist. `value` is a plain `float`; text-like info (e.g. player names) goes in `entity_refs`.
- **NarrativeItem:** mutable (status changes). `fact_ids` has `min_length=1` — a line must cite at
  least one Fact. Defaults: `status=DRAFT`, `degraded=False`.
- **Provenance chain enforced by types:** Event → Fact (`source_event_ids`) → NarrativeItem
  (`fact_ids`). The Critic can verify by lookup rather than trust. Don't weaken these constraints.

### Stats and MatchState (`mid.stats`, `mid.pipeline`)
- `calculations.py`: pure calculators (`calc_possession_share`, `calc_pass_completion`,
  `calc_pass_distance`, `calc_pass_difficulty`, `calc_pressure`, `calc_tempo`,
  `calc_shot_conversion`) each take the events so far and return Facts. `CALCULATORS` maps each to
  the event types that affect it; `calc_all(events, event_type, new_minute)` runs only those
  (time-dependent ones, pressure and tempo, also refresh when the minute advances).
- Attack direction comes from `event.period` via `models.pitch.attack_direction` (shared with the
  generator). Distances are in pitch units (120x80), labelled `m` for now.
- `MatchState.update(event)` updates counters (shots, passes, cards split yellow/red, ...), appends
  to `events`, refreshes affected Facts, and returns the Facts that changed. `facts` holds the
  latest Fact per (kind, scope); `fact_log` is append-only history (a Fact is logged only when its
  value or sources changed) and `facts_by_id` looks up any Fact ever produced. Use
  `get_fact(FactKind.X, FactScope.Y)` (scope defaults to match).

### Generator (`mid.generator`)
- `generate_match(seed, match_id=None) -> list[Event]`; `write_match` / `read_match` for JSONL
  (one Event per line; reading re-validates every line).
- **Model:** pitch 120x80, teams `home`/`away` alternate possessions (4–15 actions each); pass
  success falls with distance (clamped 0.5–0.95); 25% carry after a pass; 30% shot chance in box;
  shot outcomes 12% goal / 35% saved / 20% blocked / rest off target; 7% foul on turnover, 25%
  card on foul (10% of cards red). Sides swap at half-time (`period` 1 then 2); each half is 45 min + random stoppage (~90–100 min total).
- **Links:** goal/save events point to their shot via `related_event_id`; a pass links to the
  previous pass; a shot links to its setup pass.
- Players are anonymous labels (`Home #07`; keeper is `#01`). Coordinates clamped and rounded to 1 dp.
- **Generates clean events only** — no duplicates, out-of-order times, or off-pitch coordinates.
  Ingest's known-fault fixture (SPEC §Testing) needs a fault-injection path or hand-built fixture.

### How seeding works
- `generate_match` builds `_MatchBuilder(random.Random(seed), match_id or f"match-{seed}")`. The
  RNG is a **private instance** (not global `random`), and every random decision goes through it
  (match length, pass targets, success rolls, shot/foul/card rolls, player choice, clock steps).
- Timestamps are `KICKOFF + _clock` seconds, with `KICKOFF = 2026-10-20 15:00 UTC` fixed — no
  `datetime.now()`, `uuid`, or global RNG anywhere. Same seed → byte-identical JSONL.
- Event ids are `<match_id>-e00001…`; `match_id` changes ids but not gameplay.
- **Caveat:** seeds are not stable across generator code changes. Changing any probability
  constant or adding/removing an `rng` call shifts the whole draw sequence, so seed 1 yields a
  different match. Tests only check same-seed equality, not fixed content. For the demo, commit
  or save the generated JSONL rather than regenerating, and update the end-to-end snapshot
  whenever generator logic changes.

### Tests
- `test_generator.py`: determinism (events + file bytes), different seeds differ, JSONL round-trip,
  time order, unique ids, coords on pitch, related ids point backward, goal/save↔shot linkage,
  ~90 min length, realistic shape (1000–4000 events, >100 passes per team), CLI generate.
- `test_models.py`: JSON round-trips, frozen/forbid, invalid values rejected, Fact/Narrative
  provenance minimums, enum vocab matches spec.
- `test_scaffold.py`: `--help`, subcommand registration, Settings defaults/validation/from_env.
- `test_calculations.py`: hand-computed values per calculator, period/direction handling, Fact id
  uniqueness, Facts valid on a generated match. `test_match_state.py`: counters, yellow/red cards,
  fact accumulation, stable ids, append-only `fact_log`. `test_ingest.py`: dedupe, ordering,
  plausibility filters.
- **Known issues:** `test_ingest.py` imports `mid.validator` (should be `mid.ingest.validator`);
  `Settings` requires `llm_backend` so `test_settings_defaults` fails; a few ruff errors remain.

### Commands
- `uv run mid`-style CLI: `uv run python -m mid generate --seed 1`
- Tests: `uv run pytest`
- Lint: `uv run ruff check src tests` (ruff has no `run` subcommand; `uv run ruff check <paths>`)

## Next up
Finish Ingest: structured `quality_log` (reason codes, returned by ingest and held in MatchState),
a fault fixture with expected rejections, per-event (live) validation, `related_event_id` and
ts-vs-minute checks. Then Producer (moment scoring, cooldowns, `NarrationRequest`), the agent
interface with the mock LLM, and Narrator + Critic.

## References
- Spec: `ai/docs/SPEC-V1.md`
- Official rules: https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md
