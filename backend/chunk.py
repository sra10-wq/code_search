import ast, os, sqlite3
from tqdm import tqdm

REPOS = "data/repos"
DB = "data/chunks.db"

def iter_py_files():
    for repo in os.listdir(REPOS):
        for root, _, files in os.walk(os.path.join(REPOS, repo)):
            for f in files:
                if f.endswith(".py"):
                    yield repo, os.path.join(root, f)

def extract(path):
    try:
        if os.path.getsize(path) > 1_000_000:
            return []
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:
        return []
    lines = src.splitlines()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start, end = node.lineno, node.end_lineno
            if end - start < 2:
                continue
            code = "\n".join(lines[start - 1:end])
            out.append((node.name, start, end, code,
                        ast.get_docstring(node) or ""))
    return out

conn = sqlite3.connect(DB)
conn.execute("DROP TABLE IF EXISTS chunks")
conn.execute("""CREATE TABLE chunks (
    id INTEGER PRIMARY KEY, repo TEXT, path TEXT, name TEXT,
    start_line INT, end_line INT, code TEXT, docstring TEXT)""")

for repo, path in tqdm(list(iter_py_files())):
    rel = os.path.relpath(path, os.path.join(REPOS, repo))
    for name, s, e, code, doc in extract(path):
        conn.execute(
            "INSERT INTO chunks (repo,path,name,start_line,end_line,code,docstring) "
            "VALUES (?,?,?,?,?,?,?)",
            (repo.replace("__", "/"), rel, name, s, e, code, doc))
conn.commit()
print("chunks:", conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
