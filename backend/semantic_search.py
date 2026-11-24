import os, re, sqlite3, sys
import torch
import numpy as np, faiss
from sentence_transformers import SentenceTransformer

DB = "data/chunks.db"
INDEX = "data/vectors.faiss"
IDS = "data/vector_ids.npy"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
def model():
    global _model
    if _model is None:
        device = os.environ.get("DEVICE") or ("mps" if torch.backends.mps.is_available() else "cpu")
        _model = SentenceTransformer(MODEL, device=device)
        _model.max_seq_length = 256
    return _model

def chunk_text(name, doc, code):
    # name + docstring carry the most meaning; add the start of the code
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ")
    return f"{name}\n{doc}\n{code[:800]}"

def build_index():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT id, name, docstring, code FROM chunks").fetchall()
    ids = np.array([r[0] for r in rows], dtype=np.int64)
    texts = [chunk_text(n, d, c) for _, n, d, c in rows]
    vecs = model().encode(texts, batch_size=128, show_progress_bar=True,
                          normalize_embeddings=True, convert_to_numpy=True)
    index = faiss.IndexFlatIP(vecs.shape[1])  # inner product = cosine on normalized vectors
    index.add(vecs.astype(np.float32))
    faiss.write_index(index, INDEX)
    np.save(IDS, ids)
    print("indexed", len(ids), "chunks")

_index, _ids = None, None
def semantic_search(query, k=10):
    global _index, _ids
    if _index is None:
        _index, _ids = faiss.read_index(INDEX), np.load(IDS)
    q = model().encode([query], normalize_embeddings=True).astype(np.float32)
    scores, pos = _index.search(q, k)
    conn = sqlite3.connect(DB)
    out = []
    for score, p in zip(scores[0], pos[0]):
        cid = int(_ids[p])
        repo, path, name, line = conn.execute(
            "SELECT repo, path, name, start_line FROM chunks WHERE id=?", (cid,)).fetchone()
        out.append((cid, repo, path, name, line, float(score)))
    return out

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build_index()
    else:
        for r in semantic_search(" ".join(sys.argv[1:])):
            print(f"{r[5]:5.3f}  {r[1]}/{r[2]}:{r[4]}  {r[3]}")
