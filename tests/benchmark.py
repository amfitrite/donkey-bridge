import os
import tempfile
from donkeybridge.core import DonkeyBridge, estimate_tokens

def generate_lorem_ipsum(words_count: int) -> str:
    word = "lorem ipsum dolor sit amet consectetur adipiscing elit "
    return (word * (words_count // len(word.split()) + 1))[:words_count * 6]

def run_benchmark():
    print("Running Donkey Bridge VRAM / Context Token Savings Benchmark...")
    print("-" * 60)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name

    db = DonkeyBridge(db_path)

    # Simulate adding 100 knowledge blocks (equivalent to Baseline 1 in README)
    # Each block is ~500 tokens (approx 2000 characters)

    total_baseline_tokens = 0

    for i in range(1, 101):
        acronym = f"BLOCK{i}"
        peta = f"B=Block; {i}=Number {i}"

        # 2000 chars is roughly 500 tokens with our estimate (len/4)
        isi = generate_lorem_ipsum(333) # 333 words * 6 ~ 2000 chars

        db.add(acronym, peta, isi, tags=f"benchmark sim{i}")
        total_baseline_tokens += estimate_tokens(isi)

    # Add context overhead (e.g. Chat prompt base = 4k tokens)
    chat_overhead = 4000
    baseline_total = total_baseline_tokens + chat_overhead

    # Donkey Bridge usage: index all 100 acronyms in context + 1 active block
    idx_str = db.index()
    donkey_index_tokens = estimate_tokens(idx_str)

    # Assume 1 active block is loaded
    active_block = db.open(1)
    active_block_tokens = estimate_tokens(active_block)

    donkey_total = chat_overhead + donkey_index_tokens + active_block_tokens

    print(f"Scenario: 100 knowledge blocks × 500 tok + chat")
    print(f"Baseline Context Tokens:      {baseline_total:,}")
    print(f"Donkey Bridge Context Tokens: {donkey_total:,}")

    saved_tokens = baseline_total - donkey_total
    saved_pct = (saved_tokens / baseline_total) * 100

    print(f"Tokens Saved in Context:      {saved_tokens:,} ({saved_pct:.1f}%)")
    print("-" * 60)

    # Internal DB stats (SSD vs Context)
    stats = db.stats()
    print("Database Level Savings (SSD vs Acronyms):")
    print(f"Total Context Tokens used by Acronyms: {stats['context_tokens_used']:,}")
    print(f"Total Payload Tokens sleeping on SSD:  {stats['payload_tokens_on_ssd']:,}")
    print(f"Database Savings %:                    {stats['savings_percent']:.1f}%")

    # Cleanup
    db.conn.close()
    os.unlink(db_path)

if __name__ == "__main__":
    run_benchmark()
