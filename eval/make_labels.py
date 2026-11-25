import os, sys, csv
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("DEVICE", "cpu")
sys.path.insert(0, "backend")
from keyword_search import keyword_search
from semantic_search import semantic_search
from hybrid_search import hybrid_search

QUERIES = [
    "parse command line arguments", "read a csv file", "retry an http request",
    "load a yaml config file", "write json to a file", "resize an image",
    "compute cosine similarity", "tokenize text", "send an email",
    "connect to a database", "hash a password", "download a file from a url",
    "parse a date string", "create a directory if it does not exist",
    "read environment variables", "set up logging", "run a shell command",
    "validate an email address", "paginate api results", "cache function results",
    "rate limit requests", "compute file checksum", "extract a zip archive",
    "split a dataset into train and test", "normalize a vector",
    "save a model checkpoint", "load a pretrained model", "learning rate schedule",
    "split a list into chunks", "flatten a nested dictionary", "merge two dictionaries",
    "convert markdown to html", "extract text from a pdf", "parse html",
    "handle websocket messages", "start an async http server",
    "authenticate with an api key", "refresh an oauth token",
    "encode an image as base64", "stream a response from an llm",
    "count tokens in a prompt", "truncate text to a max length",
    "remove duplicates from a list", "generate a random string",
    "measure execution time", "watch a directory for file changes",
    "schedule a periodic task", "parse a git diff",
    "compute iou of bounding boxes", "escape html characters",
]

rows = []
for q in QUERIES:
    found = {}
    for method, fn in (("keyword", keyword_search), ("semantic", semantic_search),
                       ("hybrid", hybrid_search)):
        for r in fn(q, 10):
            cid, repo, path, name = r[0], r[1], r[2], r[3]
            entry = found.setdefault(cid, {"query": q, "id": cid, "repo": repo,
                                           "path": path, "name": name, "methods": []})
            entry["methods"].append(method)
    for e in found.values():
        e["methods"] = "+".join(e["methods"])
        e["relevant"] = ""
        rows.append(e)

with open("eval/labels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["query", "id", "repo", "path", "name", "methods", "relevant"])
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} rows to label across {len(QUERIES)} queries -> eval/labels.csv")
