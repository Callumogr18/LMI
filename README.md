# Live Match Intelligence Desk

Turns a stream of **synthetic** football match events into explainable, verified, personalized
commentary on a broadcast-style web panel. Built for the *Inside the Game* hackathon
(Microsoft x Premier League).

*Every moment explained, every claim verified, every fan served.*

## What it does

- Replays a synthetic match as a timed event stream.
- Validates the events and computes football stats, each tied back to the events it came from.
- Uses LLM agents to write commentary that cites those stats.
- A Critic checks every line against the facts and blocks anything unverified before it is published.
- Delivers the same intelligence in English and Spanish, for an analyst or a casual fan.

Code does the logic and LLMs only write the language, so no number appears that was not computed.

## Pipeline

```
Replayer -> Ingest -> Stats -> Producer -> Narrator -> Critic -> Personalizer -> Localizer -> Publisher -> Web panel
```

Full design and plan: [`ai/docs/SPEC-V1.md`](ai/docs/SPEC-V1.md). Project orientation:
[`ai/knowledge/AGENT.md`](ai/knowledge/AGENT.md).

## Status

| Done | In progress / planned |
|------|-----------------------|
| Data models (Event, Fact, NarrativeItem) | Ingest validation |
| Seeded synthetic match generator | Stats, Replayer, Producer |
| CLI and settings | Agents (Narrator, Critic, Personalizer, Localizer) |
| | Web panel, Azure deployment |

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
# Generate a seeded synthetic match (same seed = identical match)
uv run python -m mid generate --seed 1

# Run tests and lint
uv run pytest
uv run ruff check src tests
```

`replay` and `serve` commands are registered but not implemented yet.

## Configuration

Set through environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MID_LLM_BACKEND` | `mock` | `mock` or `foundry` |
| `MID_DATA_DIR` | `data` | Where generated matches are written |
| `MID_REPLAY_SPEED` | `1.0` | Replay speed multiplier |
| `MID_NARRATION_COOLDOWN_MINUTES` | `3.0` | Minimum gap between narrated moments |
| `MID_MAX_NARRATOR_RETRIES` | `1` | Narrator retries before template fallback |

## Data

All match data is synthetic. No real match data or video footage is used.
