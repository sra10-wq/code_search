import re, sqlite3, sys

DB = "data/chunks.db"
STOP = {"a","an","the","and","or","on","in","of","to","for","with","is","it","from","by","at","as","be","this","that","how","do","i"}

def split_identifiers(text):
    # parseJsonFile -> parse Json File; read_csv -> read csv
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return text.replace("_", " ")

def build_index():
    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS chunks_fts")
    conn.execute("""CREATE VIRTUAL TABLE chunks_fts USING fts5(
        name, docstring, code, tokenize='porter unicode61')""")
    rows = conn.execute("SELECT id, name, docstring, code FROM chunks")
    conn.executemany(
        "INSERT INTO chunks_fts(rowid, name, docstring, code) VALUES (?,?,?,?)",
        ((i, split_identifiers(n), d, split_identifiers(c)) for i, n, d, c in rows))
    conn.commit()
    print("FTS index built")

def keyword_search(query, k=10):
    conn = sqlite3.connect(DB)
    words = [w for w in re.findall(r"\w+", split_identifiers(query)) if w.lower() not in STOP]
    if not words:
        return []
    fts_query = " OR ".join(f'"{w}"' for w in words)
    # bm25 weights: name matches count most, then docstring, then code
    return conn.execute("""
        SELECT c.id, c.repo, c.path, c.name, c.start_line,
               bm25(chunks_fts, 10.0, 5.0, 1.0) AS score
        FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid
        WHERE chunks_fts MATCH ?
        ORDER BY score LIMIT ?""", (fts_query, k)).fetchall()

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build_index()
    else:
        for r in keyword_search(" ".join(sys.argv[1:])):
            print(f"{r[5]:7.2f}  {r[1]}/{r[2]}:{r[4]}  {r[3]}")
