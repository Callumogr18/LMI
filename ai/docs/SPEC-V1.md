# SPEC-V1: Live Match Intelligence Desk

**Hackathon:** Inside the Game (Microsoft × Premier League)

**Key dates (PT):**
- Registration closes **2026-10-20 12:00 PM** (today — must be registered before building counts).
- Submission due **2026-10-27 11:59 PM**.
- Judging **2026-10-27 → 2026-11-10**: the live test link must stay public, free, and working the whole time.

**Eligibility notes:** Team of up to 4; one Representative submits. Project must be **newly created after 2026-09-29** (registration open) and not derived from work the Sponsor funded or licensed before submission.

## Decisions
- **Event data:** existing synthetic set if a verified one is found; otherwise a small in-repo generator. Data must be **synthetic and football-realistic** (rule 4.7). No real match data; no video Footage (we scope auto-eventing out, so the Footage-rights clause in 4.7 does not apply to us).
- **Second language:** Spanish.
- **Front end:** broadcast-style panel with **two personalized experiences** — Analyst mode and Fan mode — plus EN/ES, a live stats side panel, and an agent trace view.

## Targets (prize categories)
- **Grand Prize** (First/Second) — primary ambition.
- **Best Multi-Agent System** — primary category (distinct agent roles, shared state, handoffs, failure recovery).
- **Best Use of Microsoft Foundry** — we deploy our LLM agents on Foundry, so compete here.
- **Best Enterprise Solution** — reliability, transparency, controls, path to adoption.
- **Best Azure Cloud Native Integration** — Container Apps + Azure services.

Note: an entrant can win at most one Grand Prize and one Category Prize, so categories are framed as evidence angles, not separate builds.

## Scope
- **In:** one synthetic match replayed as a timed stream; deterministic Ingest/Stats/Producer; LLM Narrator, Critic, Localizer, and Personalizer; EN + ES; dual-audience web panel (Analyst + Fan).
- **Out:** video auto-eventing, broadcast overlay graphics, multi-match, accounts.

## How it maps to the official five-stage challenge (4.1)
- **Ingest** → Replayer + Ingest (validate and correct the synthetic event stream live).
- **Interpret** → Stats (events into football statistics, patterns, and context).
- **Explain** → Producer + Narrator + Critic (why a moment matters, not just that it happened, with every claim verified).
- **Render** → Publisher + Web panel (insight that sits on screen alongside the match).
- **Personalize** → Personalizer agent + panel modes (same intelligence as two distinct experiences — analyst and casual fan — in EN or ES).

## Benefits
- Every line cites facts and is verified before publishing.
- Deterministic stats are reproducible and unit-tested.
- Retry then template fallback keeps the feed live on LLM failure.
- Clear split: code for logic, LLMs for language.
- Grounding core extends to multilingual verification and to per-audience rewrites without re-deriving facts.

## Architecture
Replayer → Ingest → Stats → Producer → Narrator (LLM) → Critic (rules + LLM) → Personalizer (LLM) → Localizer (LLM) → Publisher → Web panel

- All stages read/write a shared **MatchState** (shared-state coordination for the multi-agent category).
- Agents communicate over a declared contract (A2A-style messages / MCP tool calls) so handoffs are explicit and traceable.

## Data model
- **Event:** id, match_id, minute, second, type, team, player, x, y, end_x, end_y, outcome, related_event_id, ts
- **Fact:** id, kind, value, unit, entity_refs, source_event_ids, minute
- **Narrative item:** id, text, lang, audience (analyst|fan), fact_ids, moment_type, priority, status (draft|approved|rejected|fallback), degraded

## Stages
- **Ingest (code):** schema, duplicates, monotonic time, physical plausibility, corrections; rejections go to quality_log.
- **Stats (code):** pass distance/completion/difficulty, shot speed, possession share, pressure, tempo; emits Facts with source_event_ids.
- **Producer (code, rules):** scores moments, cooldowns, logs why each was chosen; emits NarrationRequest.
- **Narrator (LLM):** input is the NarrationRequest only; structured JSON; cites fact IDs; low temperature.
- **Critic (rules + LLM):** deterministic number/name/fact-ID checks first, then an LLM check for unsupported paraphrased claims; verdict approved|rejected|fallback.
- **Personalizer (LLM):** from the approved analyst line + the same Facts, produces a casual Fan rendering (plainer language, context, no fabricated numbers); Critic re-verifies the Fan line against the same Facts.
- **Localizer (LLM):** Spanish generated from the approved text + the same Facts; numbers and names must match; glossary maps player names and club nicknames to canonical forms.
- **Recovery:** retry once with the Critic's reason, then template fallback; any LLM error or timeout goes to fallback with a degraded flag (demonstrates "recovery from failures").

## Personalization & multi-language
- **Analyst mode:** dense, metric-forward lines; shows the Facts and the Critic verdict inline.
- **Fan mode:** concise, explanatory lines that say why the moment matters; same underlying Facts, never new numbers.
- Both modes available in **EN and ES**; Critic runs on every audience/language variant so numbers and names stay consistent.

## Panel (broadcast-style)
- Main feed of approved lines with **audience toggle (Analyst/Fan)** and **language toggle (EN/ES)**.
- Stats side panel updating live.
- Trace view: each stage's input/output and handoffs (multi-agent evidence).
- Each line shows cited facts and Critic verdict; degraded items marked.
- Quality log counter showing faults caught.
- Accessible by design: keyboard navigation, sufficient contrast, readable at broadcast distance (supports the Grand Prize "accessible experiences" language).

## Azure mapping
- **Orchestration:** Microsoft Agent Framework (Narrator, Critic, Personalizer, Localizer).
- **Agent tooling:** Azure MCP for tool/data access where it strengthens the agent contract.
- **LLM:** Microsoft Foundry deployment (Best Use of Foundry evidence — faster iteration, managed models).
- **Transport:** Event Hubs (optional; in-process queue for local dev).
- **Storage:** Cosmos DB or Azure SQL.
- **Hosting:** Azure Container Apps (this also serves the required public test link).
- **Observability:** Application Insights.
- Build local first with a mock LLM, then swap in Foundry.
- **Enterprise controls:** every published line carries provenance (fact IDs + verdict); quality_log and trace are retained; config-driven thresholds — all cited as the reliability/transparency story.

## Submission checklist (rule 4.4 — do not skip)
- Public GitHub repository.
- Demo video **under 2 minutes**, hosted publicly on YouTube/Vimeo/Facebook Video/Youku.
- Written pitch stating what was built, the problem it solves, and **which Microsoft/Azure technologies** were used (Foundry, Agent Framework, Azure MCP, Container Apps, Cosmos/SQL, App Insights, Event Hubs).
- **Live test link**: public, free, unrestricted, and working through the end of judging (2026-11-10); include any credentials if access is gated.
- Confirm all synthetic data and any third-party assets/music are cleared and licensed.

## Judging evidence (five criteria, 20% each)
- **Technological Implementation (20%):** hero-tech use — Foundry, Agent Framework, Azure MCP, Container Apps, Azure data; data-quality and code-quality shown via tests.
- **Agentic Design & Innovation (20%):** four distinct agent roles, shared MatchState, explicit A2A/MCP handoffs, retry-then-fallback recovery; written note on which steps are agents and why the rest are code.
- **Real-World Impact & Applicability (20%):** how the pipeline plugs into a live feed; enterprise provenance/controls; production-readiness via Container Apps deploy.
- **User Experience & Presentation (20%):** broadcast-style dual-audience panel, EN/ES, trace view; clear sub-2-min demo; frontend/backend balance.
- **Adherence to Category (20%):** explicit mapping to the five official stages (above) and to each target category's description.

## Testing
- Stats unit tests against hand-computed values.
- Ingest fixture with known faults and expected rejections.
- Producer tests on a fixed sequence.
- Critic tests on good/bad items with expected verdicts, across EN/ES and Analyst/Fan variants.
- Seeded end-to-end replay snapshot.

## Plan (build window ~2026-10-20 → 2026-10-27)
1. Generator + schema + Ingest
2. Stats + MatchState + Replayer
3. Producer + mock Narrator + fallbacks
4. Critic + retry/fallback
5. Foundry Narrator + Personalizer (Analyst/Fan) + Localizer (Spanish) + panel (cut line: ES before Fan mode if time-pressed)
6. Azure deploy + tracing + enterprise provenance + polish
7. Demo video (<2 min), public pitch, confirm live test link, submit

## Risks
- Crowded theme (explainable commentary) — personalization + verified multilingual output is our differentiator.
- Scope for one week; UX/Presentation is a full 20% of the score.
- Must clearly show where agents add value (trace view carries this).
- No verified synthetic dataset yet; generator is the fallback.
- Live test link must stay up through 2026-11-10 — budget Container Apps for the full judging window.
