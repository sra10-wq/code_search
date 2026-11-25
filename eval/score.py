import os, sys, csv, time, statistics
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("DEVICE", "cpu")
sys.path.insert(0, "backend")
from keyword_search import keyword_search
from semantic_search import semantic_search
from hybrid_search import hybrid_search

# load labels; only score queries where every row has a 0 or 1
labels, complete = {}, {}
with open("eval/labels.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        q, rel = row["query"], row["relevant"].strip()
        complete.setdefault(q, True)
        if rel in ("0", "1", "0.0", "1.0"):
            labels[(q, int(row["id"]))] = int(float(rel))
        else:
            complete[q] = False
queries = [q for q, done in complete.items() if done]
print(f"Scoring {len(queries)} fully labeled queries\n")

methods = {"keyword": keyword_search, "semantic": semantic_search, "hybrid": hybrid_search}
semantic_search("warmup")
for name, fn in methods.items():
    p10s, rrs = [], []
    for q in queries:
        ids = [r[0] for r in fn(q, 10)]
        rels = [labels.get((q, i), 0) for i in ids]
        p10s.append(sum(rels) / 10)
        rrs.append(next((1 / (k + 1) for k, r in enumerate(rels) if r), 0))
    print(f"{name:9s}  Precision@10 = {statistics.mean(p10s):.3f}   MRR = {statistics.mean(rrs):.3f}")

# latency: 5 timed runs per query for hybrid search
times = []
for q in queries:
    for _ in range(5):
        t = time.perf_counter(); hybrid_search(q, 10)
        times.append((time.perf_counter() - t) * 1000)
times.sort()
p95 = times[int(len(times) * 0.95) - 1]
print(f"\nhybrid latency over {len(times)} runs: median {statistics.median(times):.0f} ms, p95 {p95:.0f} ms")
