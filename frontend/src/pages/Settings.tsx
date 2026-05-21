import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getSettings, putSettings } from "../api";

export function Settings() {
  const [wakeWord, setWakeWord] = useState("");
  const [voiceRate, setVoiceRate] = useState(1);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getSettings()
      .then((s) => {
        setWakeWord(s.wake_word);
        setVoiceRate(s.voice_rate ?? 1);
      })
      .catch(() => setMsg("Could not load settings"));
  }, []);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await putSettings({ wake_word: wakeWord.trim(), voice_rate: voiceRate });
      setMsg("Saved.");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Settings</h1>
        <p className="muted">Wake word and speech rate for browser TTS.</p>
      </header>

      <form className="card form-stack" onSubmit={(e) => void save(e)}>
        <label className="label">
          Wake word
          <input
            className="input"
            value={wakeWord}
            onChange={(e) => setWakeWord(e.target.value)}
            placeholder="hey suku"
            required
          />
        </label>
        <label className="label">
          Voice rate (0 = slower, 2 = faster)
          <input
            type="range"
            min={0}
            max={2}
            step={1}
            value={voiceRate}
            onChange={(e) => setVoiceRate(Number(e.target.value))}
          />
        </label>
        <button type="submit" className="btn primary" disabled={busy}>
          {busy ? "Saving…" : "Save"}
        </button>
        {msg && <p className={msg === "Saved." ? "success" : "error"}>{msg}</p>}
      </form>

      <div className="card muted small">
        <p>
          <strong>Google search (recommended):</strong> add <code className="code">GOOGLE_SEARCH_API_KEY</code> and{" "}
          <code className="code">GOOGLE_CSE_ID</code> to <code className="code">backend/.env</code>. The key enables the
          Custom Search JSON API on the server for voice answers and summaries; the CSE id is your search engine (
          <code className="code">cx</code>). Optional: <code className="code">VITE_GOOGLE_CSE_ID</code> in{" "}
          <code className="code">frontend/.env</code> for the embedded search box (defaults are set in the Search
          page).
        </p>
        <p style={{ marginTop: "0.75rem" }}>
          Without those, the app falls back to DuckDuckGo (can rate-limit). Optional LLM:{" "}
          <code className="code">GEMINI_API_KEY</code> or <code className="code">OPENAI_API_KEY</code>.
        </p>
        <p style={{ marginTop: "0.75rem" }}>
          <Link to="/search">Open Web search page</Link> for the Google box and “Get answer”.
        </p>
      </div>
    </div>
  );
}
