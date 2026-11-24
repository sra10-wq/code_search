import re, sqlite3, sys

DB = "data/chunks.db"
STOP = {"a","an","the","and","or","on","in","of","to","for","with","is","it",
        "from","by","at","as","be","this","that","how","do","i"}

def split_identifiers(text):
    # parseJsonFile -> parse Json File; read_csv -> read csv
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return text.replace("_", " ")

def set_rank(conn):
    # name matches count most, then docstring, then code
    conn.execute("INSERT INTO chunks_fts(chunks_fts, rank) VALUES('rank', 'bm25(10.0, 5.0, 1.0)')")
    conn.commit()

def build_index():
    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS chunks_fts")
    conn.execute("""CREATE VIRTUAL TABLE chunks_fts USING fts5(
        name, docstring, code, tokenize='porter unicode61')""")
    rows = conn.execute("SELECT id, name, docstring, code FROM chunks")
    conn.executemany(
        "INSERT INTO chunks_fts(rowid, name, docstring, code) VALUES (?,?,?,?)",
        ((i, split_identifiers(n), d, split_identifiers(c)) for i, n, d, c in rows))
    set_rank(conn)
    print("FTS index built")

_conn = None
def keyword_search(query, k=10):
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB, check_same_thread=False)
    words = [w for w in re.findall(r"\w+", split_identifiers(query)) if w.lower() not in STOP]
    if not words:
        return []
    fts_query = " OR ".join(f'"{w}"' for w in words)
    # rank the top k inside the FTS index first, then join only those rows
    return _conn.execute("""
        SELECT c.id, c.repo, c.path, c.name, c.start_line, f.rank
        FROM (SELECT rowid, rank FROM chunks_fts
              WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?) f
        JOIN chunks c ON c.id = f.rowid
        ORDER BY f.rank""", (fts_query, k)).fetchall()

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build_index()
    elif sys.argv[1] == "setrank":
        set_rank(sqlite3.connect(DB))
        print("rank set")
    else:
        for r in keyword_search(" ".join(sys.argv[1:])):
            print(f"{r[5]:7.2f}  {r[1]}/{r[2]}:{r[4]}  {r[3]}")
