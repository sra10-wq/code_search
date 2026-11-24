import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function search(e) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}&k=10`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      setData(await res.json());
    } catch (err) {
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <h1>Code Search</h1>
      <p className="sub">Hybrid keyword + semantic search over 100 Python repositories</p>
      <form onSubmit={search} className="bar">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. retry an http request with backoff"
          autoFocus
        />
        <button disabled={loading}>{loading ? "Searching…" : "Search"}</button>
      </form>

      {error && <p className="error">{error}</p>}
      {data && (
        <p className="meta">
          {data.results.length} results in {data.took_ms} ms
        </p>
      )}

      {data?.results.map((r) => (
        <article key={r.id} className="result">
          <header>
            <a href={r.url} target="_blank" rel="noreferrer">
              <strong>{r.name}</strong>
            </a>
            <span className="path">
              {r.repo} / {r.path}:{r.start_line}
            </span>
          </header>
          <SyntaxHighlighter
            language="python"
            style={oneLight}
            showLineNumbers
            startingLineNumber={r.start_line}
            customStyle={{ maxHeight: 280, fontSize: 13, margin: 0 }}
          >
            {r.code}
          </SyntaxHighlighter>
        </article>
      ))}
    </main>
  );
}
