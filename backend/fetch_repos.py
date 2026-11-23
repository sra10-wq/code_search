import os, subprocess, requests
from tqdm import tqdm

HEADERS = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
OUT = "data/repos"

def top_repos(n=100):
    repos, page = [], 1
    while len(repos) < n:
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": "language:python stars:>1000 size:<50000",
                    "sort": "stars", "per_page": 100, "page": page},
            headers=HEADERS)
        r.raise_for_status()
        repos += r.json()["items"]
        page += 1
    return repos[:n]

for repo in tqdm(top_repos()):
    dest = os.path.join(OUT, repo["full_name"].replace("/", "__"))
    if not os.path.exists(dest):
        subprocess.run(["git", "clone", "--depth", "1", "-q",
                        repo["clone_url"], dest])
