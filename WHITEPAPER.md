# Donkey Bridge: Eselsbrücke Memory for AI Agents

*A mnemonic memory library for token- and VRAM-constrained agents.*

**White Paper v0.1 — October 2026 — Design validated against cognitive-science research; implementation pending.**

---

## 1. Executive summary

**Donkey Bridge** is a small Python library (target: under 500 lines, zero dependencies) that gives an AI agent a *donkey bridge* — an Eselsbrücke — as the primary format of long-term memory. It applies the oldest human memory technique to the newest expensive resource: the LLM context window.

```
In the LLM context : acronym + peta (decode map) only        (≈12 tokens per entry)
Asleep on the SSD  : full payload                            (SQLite WAL, FTS5, no deps)
When called        : stage 1 — the map; stage 2 — full payload only if the map is insufficient
```

Estimated effect: **85–97% of knowledge tokens** that would otherwise sit in context are removed; **≈20–60% total VRAM** on a local 14B model (quantized); **≈90% token cost** on API models.

The design is not a metaphor stretched over Silicon. Every decision maps onto an established memory-research result (§4) and onto independent evidence that the pattern works for LLMs (§6).

## 2. The problem

An LLM agent suffers anterograde amnesia: every session starts from zero, and within a session the context window is the scarcest resource. The three standard approaches each fail differently:

1. **Lossy summarization** — compress 80k tokens into 5k and 94% of the detail is gone forever. Asked about a specific line from turn 30, the agent can only apologize.
2. **Embedding-based RAG** — recalls well, but loads an embedding model, vector index, and often a server; it spends the very RAM/VRAM the goal was to save.
3. **Heavy memory daemons** — infrastructural overhead, background processes, dashboards. Memory management becomes a product instead of a library.

The niche left open: *what format should the stored memory have?* Existing projects store raw facts, embeddings, or machine-native symbol codes. None stores knowledge in the format humans found superior centuries ago: **a self-made mnemonic cue plus the payload shelved somewhere cheap.**

## 3. The old technique

*Eselsbrücke* (German, "donkey bridge"; Latin *pons asinorum*) is a mnemonic device that turns hard-to-remember information into a simple bridge that can be crossed again later. A donkey will not wade through water; the bridge gets it across anyway. The technique has several forms:

- **Acronym.** NASAKOM → **N**asionalisme, **A**gama, **KOM**unisme. One word recalls three concepts.
- **Reminder sentence.** An acrostic over the first letters of the planets; funny or strange sentences survive better.
- **Association.** Link a concept to a vivid image ("Rp100.000 used to fill a basket; now it fills half" → inflation).
- **Chunking.** Four keywords — observe → analyze → test → conclude — instead of paragraphs.

The shared procedure: *pick the material → find a pattern → build a memorable cue → test without looking at notes.* Human memory never holds the big picture; it holds the **handle** that reconstructs it.

## 4. Why it works — cognitive science

| Principle | Source | Consequence in Donkey Bridge |
|---|---|---|
| **Cue availability.** All knowledge is expressed within a retrieval context; the available cues decide what is recalled. | Karpicke & O'Day (Oxford Handbook) | `index()` is the only block that permanently lives in the prompt. |
| **Cue diagnosticity.** A cue works when it uniquely specifies the target and matches nothing else. | Nairne 2002; Goh & Lu 2012 | Uniqueness check: an exact-match FTS5 query rejects colliding acronyms before commit. |
| **Encoding specificity.** Cues are strongest when their context overlaps the encoding moment. | Tulving & Thomson 1973 | The `peta` (decode map) is written at storage time, by the same agent, in the same context. |
| **Elaboration.** Effective encoding adds distinctive, organized detail — a *mediator* between cue and target. | Craik & Lockhart 1972; Dunlosky et al. 2005 | The map is a mediator, not a summary: each piece of the acronym points at one exact item. |
| **Generation effect.** Self-generated mnemonics stick better than supplied ones. | Standard learning-science literature | The **agent constructs its own acronym**; the library only validates and stores. |
| **Retrieval practice (testing effect).** The act of retrieval, not restudy, drives retention — robust even without feedback. | Karpicke & Smith 2012 (*J. Memory & Language*); Pyc & Rawson 2010 | Stage 1 forces reconstruction from the map before `open()` is allowed to show the payload; a programmed quiz returns in Phase 2. |
| **Fuzzy-trace theory.** Humans keep a durable fuzzy gist and look up verbatim detail on demand. | Reyna & Brainerd 1995 | The map ≈ gist; the payload ≈ the original page. |
| **7±2 chunking.** Working memory carries roughly four to seven chunks. | Miller 1956 | The context window is finite in the same way; chunks are the unit carried. |

## 5. Translating the technique to AI

| Human process | Donkey Bridge mechanism |
|---|---|
| Working memory (≈7 chunks) | Context window + KV cache (billable tokens / VRAM) |
| Books on the shelf | SQLite on SSD (WAL; bytes that cost nothing to keep) |
| Mnemonic handle | Acronym + peta (≈12 tokens) |
| "I remember what the book said" | `recall()` → map; if insufficient → `open()` |
| Filling in detail from the shelf | `open(row_id)` loads the full payload |
| Browsing the shelf by title | `search()` over FTS5 (when the acronym itself is forgotten) |

**Two-stage recall is the heart.** Stage 1 returns only the decode map — usually enough, exactly like a human recalling a list from its acronym. Stage 2 loads the payload only on proof of insufficiency. The agent, not the library, decides when stage 2 is justified (SCG-MEM, 2026: recall is a generative reconstruction within a schema — so let the schema earn its keep first).

## 6. Evidence from prior work

- **ReadAgent** (Google DeepMind, ICML 2024; arXiv 2402.09727). Humans read long documents keeping a *gist memory* and look pages up interactively. Implemented purely by prompting, it raises effective context 3.5–20× across three long-document benchmarks and cuts consumed words by roughly 13–25%. This validates the general pattern: *short cues in context, full text on demand.* Donkey Bridge differs in the cue format: not an ordinary summary but an acronym + decode map — consistent with the mnemonic-cue literature, and an order of magnitude shorter.
- **Keyword Mnemonics via LLM** (UMass Amherst; arXiv 2409.13952). LLMs can produce verbal mnemonic cues comparable to human-made ones, provided *overgenerate-and-rank*: generate many candidates, rank them. This becomes the Phase-2 acronym quality loop (Phase 1 enforces the cheaper guard: uniqueness + reconstruction test).
- **SCG-MEM** (arXiv 2604.20117). "To know is to construct" — valid recall is generative within schematic structure. Supports the two-stage design: attempt reconstruction at stage 1, escalate to verbatim read at stage 2.
- **MemGen** (arXiv 2509.24704) shows memory invocation can be triggered mid-reasoning — a Phase-2+ idea for auto-recall, not needed for MVP.

No surveyed project stores memory *as mnemonics*. The nearest neighbors store path indexes (LLMFS), raw facts (agentmem, memento), machine symbol codes (MemPalace AAAK), or blobs (ai-memory-mcp). §11 details this gap.

## 7. Architecture

```text
donkey-bridge/
├── WHITEPAPER.md  ·  README.md  ·  pyproject.toml
├── donkeybridge/
│   ├── __init__.py     # public API: DonkeyBridge
│   ├── models.py       # dataclasses + token estimator (chars / 4)
│   ├── db.py           # SQLite (WAL) + FTS5 schema + sync triggers
│   ├── store.py        # add (uniqueness-checked) / forget / list
│   ├── recall.py       # recall(stage 1) · open(stage 2) · search
│   ├── index.py        # renders the acronyms-only block
│   ├── prompt.py       # the Eselsbrücke protocol template for agents
│   └── cli.py          # init / add / list / recall / open / search / index / forget / stats
└── tests/              # round-trip: add → index → recall → open → forget
```

Schema:

```sql
CREATE TABLE blocks (
  id INTEGER PRIMARY KEY,
  acronym TEXT NOT NULL,              -- "NASAKOM"
  peta    TEXT NOT NULL,              -- "N=Nasionalisme; A=Agama; KOM=Komunisme"
  isi     TEXT NOT NULL,              -- full payload; lives ONLY on SSD
  tags    TEXT NOT NULL DEFAULT '',
  tokens_est INTEGER,
  created_at TEXT, last_recall TEXT,
  recall_count INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE blocks_fts USING fts5(acronym, peta, tags);  -- kept in sync by triggers
```

Design properties:

- **`add()` is the flush.** The moment a payload is stored, it no longer needs any place in the context. There is no second flush mechanism because SSD is always the source of truth (WAL write-through).
- **No cache, no pager.** contrary to virtual-memory designs, there is nothing to evict: memory lives on disk, and only acronyms circulate.
- **Uniqueness guard (cue diagnosticity).** Exact-match lookup (case-insensitive) refuses a new acronym that collides.
- **Statistics (§10) report actual live token avoided**, not a theory.

## 8. The storage protocol (Eselsbrücke procedure for agents)

1. **Pick the material.** One `add()` carries one block: a list, an order, a definition, a procedure.
2. **Find the pattern.** The agent composes the *peta*: first letters, keywords, relations between ideas.
3. **Build a distinctive cue.** Familiar, funny, or unique wording; the uniqueness check rejects collisions.
4. **Test without notes.** Before commit, the agent must reconstruct the payload from acronym + map alone. If meanings swap, the bridge is revised first. (`prompt.py` ships this protocol as a template so every agent runs the same loop.)

## 9. API

```python
from donkeybridge import DonkeyBridge

db = DonkeyBridge("data/bridges.db")

db.add(acronym="NASAKOM",
       peta="N=Nasionalisme; A=Agama; KOM=Komunisme",
       isi="<full explanation>", tags="history politics")

db.index()                  # "NASAKOM — three pillars | DB-7 | ..."  (≈12 tok/entry)
db.recall("NASAKOM")        # stage 1: the map only (+ row id)
db.open(row_id)             # stage 2: full payload, only if justified
db.search("history")        # FTS5 across acronym, map, tags
db.forget(row_id)
db.stats()                  # live token/VRAM savings report
```

CLI mirrors the API one-to-one. Python ≥ 3.10; `sqlite3`, `json`, `argparse` only.

## 10. Resource analysis

```
KV cache per token (f16) = 2 × layers × kv_heads × head_dim × 2 bytes
Qwen2.5-14B (48 L, 5 KV heads) → 120 KB/token
Qwen3-14B   (40 L, 8 KV heads) → 160 KB/token

VRAM saving (%) = (context_baseline − index − active) × KV_per_token ÷ total_VRAM_baseline
```

Assumptions in the table below: fixed chat/instruction layer of 4k tokens in both cases; payload 500 tokens per block; acronym+map ≈ 12 tokens; one active payload open while working; model weights ≈ 9.0 GB at Q4.

| Scenario | Context tokens | KV cache | Total VRAM | Saved |
|---|---|---|---|---|
| Qwen2.5-14B Q4 — baseline: 100 blocks | 54k | 6.6 GB | 15.6 GB | — |
| **Donkey Bridge (index 100 + 1 active)** | 6.2k | 0.8 GB | **9.8 GB** | **≈38%** |
| Baseline: 200 blocks | 104k | 12.2 GB | 21.2 GB | — |
| **Donkey Bridge** | 7.4k | 0.9 GB | **9.9 GB** | **≈53%** |
| Qwen3-14B Q4 — baseline: 100 blocks | 54k | 8.8 GB | 17.9 GB | — |
| **Donkey Bridge** | 6.2k | 1.0 GB | **10.0 GB** | **≈44%** |
| Baseline: 200 blocks | 104k | 17.0 GB | 26.0 GB | — |
| **Donkey Bridge** | 7.4k | 1.2 GB | **10.2 GB** | **≈61%** |

Readings:

- **Knowledge tokens** removed from context: 85–97% in all scenarios.
- **Total VRAM** saving scale with the knowledge load: ≈20% (small baseline) to ≈60% (large baseline) on 14B Q4; with 28 GB fp16 weights the *percentage* halves but the *gigabytes* saved stay the same.
- **Fit matters more than percent:** the 200-block baseline (21 GB) does not fit a 16 GB GPU; Donkey Bridge needs < 10 GB. The point is not only cheaper — it is *possible where it was not*.
- **API models:** no VRAM involved; token cost falls ≈90%.
- **What is NOT saved:** model weights. The library shrinks the context/KV side only, and says so plainly.

`stats()` turns this estimate into a running number: it compares actual stored payload tokens against the index footprint currently circulating.

## 11. Related work

| Project | Nearest to | Gap vs Donkey Bridge |
|---|---|---|
| **llmfs** | Virtual-memory analogy; light index stays in prompt, payload pages in | Index is paths/folders, not mnemonics; needs ChromaDB |
| **vMem** | OS paging via Claude Code hooks; eviction, pinning | Daemon complexity; no mnemonic format |
| **agentmem** | SQLite + FTS5, zero-dep mode, MCP owned by tool surface | Stores raw facts; no two-stage recall |
| **MemPalace / mempalace-rs** | Symbolic compression (~30× AAAK codes) | Machine codes, unreadable to a human as a bridge; palace = vector store |
| **ai-memory-mcp** | offload/deref of big blobs; TOON token format | No cognitive schema; no recall practice |
| **memento** | "bridge" between fact store and wiki | The bridge points at documents, not at memory |
| **Agent-Memory-Bridge** | Name resemblance only | Decision log, no compression |

Nobody surveyed: (a) stores memory in mnemonic format, (b) does cue→map→payload two-stage recall, (c) applies retrieval practice to agent memory. That is the verified gap (GitHub search, October 2026).

## 12. Limitations and risks

- **Acronym quality is the single point of failure.** A weak map garbles recall exactly like a misunderstood school mnemonic. Mitigations: uniqueness check + mandatory reconstruction test (Phase 1); overgenerate-and-rank (Phase 2). The payload is never lost — worst case is a full `open()`.
- **FTS5 is keyword-based.** Synonym miss when the acronym is forgotten and the tag word isn't guessed. Optional embedding fallback (Phase 4) tradeoff: it reintroduces a model dependency, so it stays off by default.
- **No weight savings.** As stated: only the context/KV/token-cost side reacts.
- **Agent discipline.** The protocol runs on prompt compliance; the library facilitates rather than enforces.
- **SQLite single-writer** suits one agent per database file; multi-agent setups get one file per agent (namespacing by file, not by schema).

## 13. Roadmap

| Phase | Scope |
|---|---|
| **MVP** | store + recall/open + search + index + CLI + tests + `stats()` |
| 2 | overgenerate-and-rank (3–5 acronym candidates, ranked) · programmed quiz (testing effect) |
| 3 | MCP server so any harness (Claude Code, OpenCode, …) can use it beyond Python |
| 4 | optional embedding fallback (off by default) · multi-database profiles |

## 14. Conclusion

Eselsbrücke survives because it matches what memory research keeps confirming: *avail yourself of a distinctive, uniquely diagnostic cue; elaborate on encode; recreate before you re-read.* Donkey Bridge carries that shape into agent infrastructure — a zero-dependency, ~400-line library in which the agent builds its own bridges, validates them by reconstructing without notes, and lets everything heavy sleep on an SSD that never bills a token. Memory savings here are not an optimization layer: **memory that is reconstructed, not carried, is the most humane form of conserving VRAM.**

## References

- Lee et al., *A Human-Inspired Reading Agent with Gist Memory of Very Long Contexts (ReadAgent)*, ICML 2024 — arXiv:2402.09727.
- Lee, J., McNichols, H., Lan, A., *Exploring Automated Keyword Mnemonics Generation with Large Language Models via Overgenerate-and-Rank*, 2024 — arXiv:2409.13952.
- Zhang, G., Fu, M., Yan, S., *MemGen: Weaving Generative Latent Memory for Self-Evolving Agents*, 2025 — arXiv:2509.24704.
- *To Know is to Construct: Schema-Constrained Generation for Agent Memory (SCG-MEM)*, 2026 — arXiv:2604.20117.
- Karpicke, J. D., O'Day, G. M., retrieval practice / cue principles chapters, *Oxford Handbook of Human Memory* (in press).
- Karpicke, J. D., Smith, M. A., *Separate mnemonic effects of retrieval practice and elaborative encoding*, Journal of Memory and Language, 2012.
- Tulving, E., Thomson, D. M., *Encoding specificity and retrieval processes in episodic memory*, Psychological Review, 1973.
- Nairne, J. S., *The functionalist agenda in memory research*, 2002; Goh, W. D., Lu, S. H. Q., 2012 (cue diagnostic value).
- Miller, G. A., *The magical number seven, plus or minus two*, Psychology Review, 1956.
- Reyna, V. F., Brainerd, C. J., *Fuzzy-trace theory*, 1995.

## Appendix A — Name provenance and availability (checked 2026-10-23)

- **GitHub** (`donkey-bridge` / `DonkeyBridge`): existing matches are a dormant placeholder organization (`DonkeyBridgeLite`, Impressum pages, no code), a dead 2017 CSS website, an empty 2024 repo, and Donkey Car projects (RC vehicles — different domain). **No memory-library namesake exists.**
- **PyPI**: `donkeybridge` returns 404 — the package name is free.
- Etymology: Eselsbrücke = "donkey bridge"; donkeys refuse to wade, so bridges were built at fords — the roundabout that proves faster. NASAKOM is a historical Indonesian mnemonic from 1960.
