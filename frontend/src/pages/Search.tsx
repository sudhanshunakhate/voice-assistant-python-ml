import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getSearchAnswer, getSearchStatus } from "../api";
import { GoogleProgrammableSearch } from "../components/GoogleProgrammableSearch";

/** Default CSE id from your embed (public; override with VITE_GOOGLE_CSE_ID). */
const DEFAULT_CX = "84e2997a64e2c425b";

export function Search() {
  const cx = (import.meta.env.VITE_GOOGLE_CSE_ID as string | undefined)?.trim() || DEFAULT_CX;
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [googleOk, setGoogleOk] = useState<boolean | null>(null);

  useEffect(() => {
    getSearchStatus()
      .then((s) => setGoogleOk(s.google_custom_search_configured))
      .catch(() => setGoogleOk(null));
  }, []);

  async function onSummarize(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setBusy(true);
    setErr(null);
    setAnswer(null);
    try {
      const { answer: a } = await getSearchAnswer(q);
      setAnswer(a);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page search-page">
      <header className="page-head">
        <h1>Web search</h1>
        <p className="muted">
          Google Programmable Search in the page, plus a short spoken-style summary from S.U.K.U (same results pipeline
          as “what is …” on the command center).
        </p>
      </header>

      <div className="card search-why">
        <h2 className="search-why-title">Why the API key and CSE ID?</h2>
        <ul className="search-why-list">
          <li>
            <strong>Search engine ID (<code className="code">cx</code> / <code className="code">GOOGLE_CSE_ID</code>)</strong>{" "}
            tells Google which Programmable Search Engine to use. It is safe to expose in the browser embed.
          </li>
          <li>
            <strong>API key (<code className="code">GOOGLE_SEARCH_API_KEY</code>)</strong> is only used on the{" "}
            <em>server</em> to call the Custom Search JSON API for snippet summaries and voice answers. It stays in{" "}
            <code className="code">backend/.env</code> — never put it in frontend code.
          </li>
          <li>
            Together they avoid DuckDuckGo rate limits and return Google-indexed snippets for the assistant.
          </li>
        </ul>
        {googleOk === true && (
          <p className="success small" style={{ marginTop: "0.75rem" }}>
            Backend reports Google Custom Search is configured.
          </p>
        )}
        {googleOk === false && (
          <p className="error small" style={{ marginTop: "0.75rem" }}>
            Backend does not see both keys in <code className="code">backend/.env</code>. Summaries fall back to
            DuckDuckGo or a wait message.
          </p>
        )}
      </div>

      <section className="card form-stack search-summary-card">
        <h2 className="search-section-title">Ask S.U.K.U (summary)</h2>
        <form onSubmit={(e) => void onSummarize(e)} className="search-summary-form">
          <label className="label">
            Question or topic
            <input
              className="input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. climate summit 2026"
              autoComplete="off"
            />
          </label>
          <button type="submit" className="btn primary" disabled={busy || !query.trim()}>
            {busy ? "Searching…" : "Get answer"}
          </button>
        </form>
        {err && <p className="error">{err}</p>}
        {answer && (
          <div className="search-answer">
            <div className="search-answer-label">Answer</div>
            <p className="search-answer-body">{answer}</p>
          </div>
        )}
      </section>

      <section className="card search-google-card">
        <h2 className="search-section-title">Google search box</h2>
        <p className="muted small" style={{ marginBottom: "1rem" }}>
          Full result pages open in Google’s widget (hosted by Google).
        </p>
        <GoogleProgrammableSearch cx={cx} />
      </section>

      <p className="muted small">
        <Link to="/">← Command center</Link>
      </p>
    </div>
  );
}
