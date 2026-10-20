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
  related_event_id, ts
- **Fact:** id, kind, value, unit, entity_refs, source_event_ids, minute
- **Narrative item:** id, text, lang, audience(analyst|fan), fact_ids, moment_type, priority,
  status(draft|approved|rejected|fallback), degraded

## Tech stack

- **Local/dev:** Python ≥ 3.12, managed with **uv** (`uv run`, `uv add`). Entry: `main.py`.
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
main.py              # placeholder entry point
pyproject.toml       # uv project, py>=3.12, no deps yet
src/                 # (empty) implementation lands here
ai/docs/SPEC-V1.md   # authoritative spec: scope, stages, plan, risks
ai/knowledge/        # orientation + reference (this file)
```

Project is greenfield — only the spec exists so far. Build order is in SPEC-V1 §Plan
(generator/schema/Ingest → Stats/MatchState/Replayer → Producer → Critic → Foundry +
Personalizer + Localizer + panel → Azure deploy → demo/submit).

## References
- Spec: `ai/docs/SPEC-V1.md`
- Official rules: https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md
