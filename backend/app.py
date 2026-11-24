import os
# must run before torch/faiss load: avoids the macOS OpenMP conflict between them
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("DEVICE", "cpu")
import sqlite3, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from hybrid_search import hybrid_search, TIMINGS
from semantic_search import semantic_search

DB = "data/chunks.db"

@asynccontextmanager
async def lifespan(app):
    semantic_search("warmup")  # load model + FAISS index once at startup
    yield

app = FastAPI(title="Code Search", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["GET"], allow_headers=["*"])
conn = sqlite3.connect(DB, check_same_thread=False)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/search")
async def search(q: str = Query(..., min_length=2), k: int = Query(10, ge=1, le=50)):
    t = time.perf_counter()
    results = hybrid_search(q, k)
    out = []
    for cid, repo, path, name, line, score in results:
        code, end = conn.execute(
            "SELECT code, end_line FROM chunks WHERE id=?", (cid,)).fetchone()
        out.append({
            "id": cid, "repo": repo, "path": path, "name": name,
            "start_line": line, "end_line": end, "score": round(score, 4),
            "code": code,
            "url": f"https://github.com/{repo}/blob/HEAD/{path}#L{line}-L{end}",
        })
    return {"query": q, "took_ms": round((time.perf_counter() - t) * 1000),
            "timings": dict(TIMINGS), "results": out}
