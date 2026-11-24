import sys, time
from keyword_search import keyword_search
from semantic_search import semantic_search

RRF_K = 60  # standard constant; dampens the gap between rank 1 and rank 2

def hybrid_search(query, k=10, pool=50):
    kw = keyword_search(query, pool)
    sem = semantic_search(query, pool)
    scores, info = {}, {}
    for results in (kw, sem):
        for rank, r in enumerate(results):
            cid = r[0]
            scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
            info[cid] = r[1:5]  # repo, path, name, start_line
    top = sorted(scores, key=scores.get, reverse=True)[:k]
    return [(cid, *info[cid], scores[cid]) for cid in top]

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])
    semantic_search("warmup")  # load model + index so timing is fair
    t = time.perf_counter()
    results = hybrid_search(query)
    ms = (time.perf_counter() - t) * 1000
    for r in results:
        print(f"{r[5]:.4f}  {r[1]}/{r[2]}:{r[4]}  {r[3]}")
    print(f"\n{ms:.0f} ms")
