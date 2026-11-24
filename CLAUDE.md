# MarketPulse

AI research assistant over SEC filings, stock prices and news sentiment. It
retrieves evidence, computes numbers in code, and answers with chunk-level
citations. A 10-day learning and portfolio project; a research/education tool,
not investment advice.

Full plan, roadmap and learning split: [docs/PLAN.md](docs/PLAN.md)

## Stack

Python 3.12, FastAPI, Postgres + pgvector, sentence-transformers, FinBERT,
Streamlit, Docker.

## Rules

- **"LLM reasons, code computes."** Numbers come from code, never from the LLM.
- Every claim cites a `chunk_id`.
- No causation claims (never say sentiment or news *caused* a price move).
- Type hints on all functions.
- pytest for logic.
- Respect the learning split in docs/PLAN.md: for those parts give signatures
  and hints only, then review what the user writes.

## How to work

- Keep code simple, readable and well-structured. No over-engineering.
- Briefly explain key decisions; the user must be able to defend every line.
- Never build ahead of the current day's scope.
- Show a plan first and wait for "go" before writing files.
- Run code and tests, and fix failures, before saying something is done.

## Current status

Day 0 in progress.
