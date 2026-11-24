# MarketPulse — Project Plan

An AI research assistant over SEC filings, stock prices and news sentiment.
Built in 10 days as a learning and portfolio project. It is a research and
education tool, **not investment advice**.

## Goal

A user asks, for example:

> "What changed in Tesla's risk factors last quarter and how did the stock react?"

The system then:

- retrieves evidence from filings, news and prices,
- computes numbers **in code** (never in the LLM),
- answers with **chunk-level citations**,
- separates facts from interpretation,
- never claims sentiment caused a price move,
- shows a "data as of" date.

## Architecture

### 1. Ingestion (scheduled)

- **Filings:** SEC EDGAR 10-K / 10-Q / 8-K for ~20 tickers → clean HTML → split
  by section (Item 1A Risk Factors, Item 7 MD&A, etc.) → chunk (500–800 tokens,
  with overlap) → embed (sentence-transformers, `BAAI/bge-small-en-v1.5`).
- **Prices:** yfinance.
- **News:** RSS / GDELT → scored by the sentiment model.

### 2. Storage

Postgres + pgvector. Tables:

| Table | Contents |
|---|---|
| `companies` | Tracked tickers |
| `documents` | One row per filing |
| `chunks` | Embedding vector + full-text `tsvector` + metadata (ticker, form, section, filed_at, url) |
| `prices` | Daily prices |
| `news` | Articles with sentiment |
| `query_logs` | Latency, tokens and cost per query |
| `eval_runs` | Evaluation results over time |

### 3. ML

TF-IDF + Logistic Regression baseline vs FinBERT (`ProsusAI/finbert`) on
Financial PhraseBank. Compare macro-F1; the best model scores all news.

### 4. Retrieval

Hybrid search = vector search + Postgres full-text, merged with Reciprocal Rank
Fusion (RRF), with metadata filters (ticker, date, form).

### 5. Agent

An LLM with tool calling. Principle: **"LLM reasons, code computes."**

| Tool | Purpose |
|---|---|
| `search_documents` | Hybrid search over filing chunks |
| `compare_filings` | Quarter-over-quarter section diff |
| `get_prices` | Price history for a ticker |
| `price_reaction` | Return around an event vs the market |
| `sentiment_summary` | Aggregate news sentiment |
| `search_live_news` | Fresh news lookup |
| `find_unexplained_moves` | Price moves with no matching event |

### 6. Citation check

Verify each claim is supported by its cited chunk; drop or label unsupported
claims. Produces a citation-accuracy metric.

### 7. API + UI

- **FastAPI:** `/ask`, `/companies`, `/prices/{ticker}`
- **Streamlit:** chat UI with sources and a Plotly price chart with event markers

### 8. Quality / ops

- 50-question eval set (`evals/questions.jsonl`)
- Metrics: recall@5, citation accuracy, agent task success
- pytest
- GitHub Actions CI running tests + evals
- Logging of latency / tokens / cost per query
- Docker Compose; deploy

## Repo structure

```
app/
  ingestion/    edgar.py, prices.py, news.py, chunker.py
  ml/           sentiment.py
  retrieval/    search.py
  agent/        loop.py, tools.py, verify.py
  api/          main.py
  db.py
ui/             streamlit_app.py
evals/
notebooks/
tests/
docs/
docker-compose.yml
CLAUDE.md
.env.example
README.md
```

## Revised roadmap (replanned Nov 24)

Day 0 was finished on Nov 15; Days 1–8 slipped. This is the 7-day plan to
Dec 1. It follows the original cut order: news sentiment, filing diffs,
unexplained moves and the scheduler move to after Dec 1. Evals and the citation
check stay in.

| Date | Scope | User writes |
|---|---|---|
| Nov 24 | `.env` + AAPL download, GitHub + CI, HTML cleaning + section splitting, ingest 10-K/10-Q for ~10 tickers, prices | DB schema |
| Nov 25 | Chunks, embeddings, full-text index | Chunker |
| Nov 26 | Hybrid search, ~30 eval questions, recall@5 | RRF + recall@k |
| Nov 27 | Cited answers + citation-accuracy metric | Citation checker |
| Nov 28 | Agent with 3 tools: `search_documents`, `get_prices`, `price_reaction` | Agent loop |
| Nov 29 | FastAPI, Streamlit + Plotly chart, Docker | — |
| Nov 30 | Deploy, README + diagram, demo GIF, full eval run | — |
| After Dec 1 | News, sentiment baseline vs FinBERT, `compare_filings`, live news, unexplained moves, scheduler | Sentiment baseline, unexplained-move logic |

Workflow: one branch and one pull request per day; CI runs pytest on every PR.

## Original 10-day roadmap

| Day | Date | Scope |
|---|---|---|
| 0 | Nov 15 | Repo, Docker Postgres + pgvector, first 10-K downloaded |
| 1 | Nov 16 | EDGAR ingestion for 20 tickers, section splitting, prices, DB schema |
| 2 | Nov 17 | Chunking, embeddings, full-text index, news ingestion |
| 3 | Nov 18 | Sentiment baseline vs FinBERT, score all news |
| 4 | Nov 19 | Hybrid retrieval + RRF + filters, 50 eval questions, recall@5 |
| 5 | Nov 20 | Cited answer generation + citation checker + accuracy metric |
| 6 | Nov 21 | Agent loop + core tools |
| 7 | Nov 22 | Freshness: live news tool, unexplained-move detector, scheduler |
| 8 | Nov 23 | FastAPI + Streamlit UI + charts |
| 9 | Nov 24 | Tests, CI with evals, caching / retries / logging / cost, Docker, deploy |
| 10 | Nov 25 | Full eval run, fix weakest area, README + diagram + demo |
| — | Nov 26–30 | Buffer, write-up, resume |

Internship applications start **Dec 1**.

### If behind

Cut in this order:

1. News-sentiment depth
2. UI polish
3. Scheduler

**Never cut the evals or the citation check.**

## Learning split

**I write these myself** (Claude gives signatures + hints only, then reviews):

- DB schema
- Chunker
- Sentiment baseline + metrics
- RRF + recall@k
- Citation checker
- Agent loop
- Unexplained-move logic

**Claude may fully write:**

- Docker / CI YAML
- HTML cleaning
- Streamlit / Plotly
- Test scaffolding
- README formatting
