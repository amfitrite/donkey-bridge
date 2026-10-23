# Donkey Bridge

**Eselsbrücke memory for AI agents.**
One small acronym rides in the context window. The full payload sleeps on your SSD.

```text
In the LLM context :  NASAKOM — N=Nasionalisme; A=Agama; KOM=Komunisme   (≈12 tokens)
Asleep on the SSD  :  the full explanation, document, or facts           (SQLite · WAL · FTS5)
When called        :  stage 1 → the peta (decode map) · stage 2 → full payload only if needed
```

> ***Eselsbrücke*** (German, "donkey bridge") — a mnemonic device that turns hard-to-remember
> information into a simple bridge you can cross again later. Donkeys famously refuse to wade
> through water, so people built small bridges at the fords: a detour that turns out to be the
> fastest route. Humans have never carried the big picture around — they store the *handle*
> that reconstructs it on demand.

## Why

Every AI agent owns a very expensive working memory — the context window (≈120–256 KB of VRAM
per token on a local model) — and a nearly free long-term shelf — the SSD. Yet most memory
tooling parks whole knowledge blocks in the window, compresses them lossily, or bolts on an
embedding stack that spends exactly the RAM/VRAM you were trying to save.

Donkey Bridge takes the oldest memory hack there is and applies it to agents:

- **Acronyms instead of payloads.** The acronym + its decode map *is* the storage format, not an optimization on top of it.
- **Two-stage recall.** First return only the decode map (a few tokens). Load the full payload only when the map proves insufficient.
- **The agent writes its own acronyms.** The generation effect: self-made mnemonics stick better. The library provides tools, the LLM provides the bridge.
- **Test without notes.** Before committing, the agent must reconstruct the payload from the acronym + map alone. If meanings swap, the bridge gets rebuilt. (Learning science: the testing effect.)
- **Zero dependencies.** Python stdlib only (`sqlite3`, `argparse`). The memory itself costs nothing to run.

## Status

🚧 **Pre-release** — repository structure and whitepaper first; implementation lands next.
Target: one small package (~400 lines), Python ≥ 3.10, no third-party dependencies.

## Planned usage

```python
from donkeybridge import DonkeyBridge

db = DonkeyBridge("data/bridges.db")

# 1. Store. add() *is* the flush: payload goes to SSD and leaves the context.
db.add(
    acronym="NASAKOM",
    peta="N=Nasionalisme; A=Agama; KOM=Komunisme",
    isi="<the full explanation, document, or facts>",
    tags="history politics",
)

# 2. The only thing that circulates in the LLM prompt: acronyms alone (≈12 tokens each).
db.index()                # → "NASAKOM — three pillars | DB-7 | ..."

# 3a. Stage 1: call the acronym → the decode map only.
db.recall("NASAKOM")      # → "N=Nasionalisme; A=Agama; KOM=Komunisme" (+ row id)

# 3b. Stage 2: only if the map is not enough → load the full payload.
db.open(db_id)

# 4. Forgot the acronym? Search by keyword (SQLite FTS5).
db.search("history")

# 5. Housekeeping
db.forget(db_id)
db.stats()                # live token-savings report, not theory
```

Planned CLI: `dkb init | add | list | recall | open | search | index | forget | stats`

## Project layout

```text
donkey-bridge/
├── WHITEPAPER.md        # the full rationale: cognitive science ↔ design decisions
├── README.md
├── pyproject.toml
├── donkeybridge/        # the library (implementation pending)
└── tests/               # round-trip tests: add → index → recall → open → forget
```

## What it saves

Estimate for a local model Qwen 14B Q4 (KV cache ≈ 120–160 KB/token at fp16):

| Scenario | Context tokens | VRAM total | Saved |
|---|---|---|---|
| Baseline: 100 knowledge blocks × 500 tok + chat | 54k | 15.6 GB | — |
| **Donkey Bridge (100 acronyms + 1 active block)** | 6.2k | **9.8 GB** | **≈38%** |
| Qwen3-14B baseline: 200 blocks (104k tok) | 104k | 26.0 GB | — |
| **Donkey Bridge** | 7.4k | **10.2 GB** | **≈61%** |

- Knowledge tokens carried in context: **85–97% fewer**, in every scenario.
- Cloud/API models: ≈ **90% lower token cost** (no VRAM involved).
- The 200-block baseline needs 21 GB — it does not fit a 16 GB GPU at all. Donkey Bridge makes it fit under 10 GB.

Full math and assumptions in [WHITEPAPER.md](WHITEPAPER.md).

## Design sources (cognitive science + prior research)

| Principle | Source | Where it lands in the design |
|---|---|---|
| Cue availability | Karpicke & O'Day (Oxford Handbook) | `index()` is the only block that always lives in the prompt |
| Cue diagnosticity | Nairne 2002; Goh & Lu 2012 | uniqueness check rejects colliding acronyms |
| Encoding specificity | Tulving & Thomson 1973 | the map is written at encode time, by the same "hand" |
| Retrieval practice / testing effect | Karpicke & Smith 2012 | reconstruct-first-before-`open()`; programmed quiz later |
| Gist memory + interactive lookup | ReadAgent — DeepMind, ICML 2024 (arXiv 2402.09727) | map = gist; payload = the page to look up |
| Keyword mnemonics via LLM | UMass Amherst (arXiv 2409.13952) | later: overgenerate-and-rank for acronym candidates |
| 7±2 chunking | Miller 1956 | limited window → chunks are the unit you carry |

## Roadmap

| Phase | Scope |
|---|---|
| **MVP** | store + recall/open + search + index + CLI + tests + `stats()` |
| 2 | overgenerate-and-rank (multiple acronym candidates, pick the best) · programmed quiz (testing effect) |
| 3 | MCP server so any agent harness can use it, not just Python |
| 4 | optional embedding fallback (off by default — stays zero-dep) |
