import { useEffect, useState } from "react";
import { clearHistory, getHistory, type MessageRow } from "../api";

export function History() {
  const [rows, setRows] = useState<MessageRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setRows(await getHistory());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onClear() {
    if (!confirm("Clear all conversation history?")) return;
    try {
      await clearHistory();
      await load();
    } catch {
      setErr("Clear failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head row-between">
        <div>
          <h1>History</h1>
          <p className="muted">Messages stored in SQLite on the server.</p>
        </div>
        <button type="button" className="btn ghost danger" onClick={() => void onClear()}>
          Clear all
        </button>
      </header>

      {err && <p className="error">{err}</p>}

      <div className="history-list">
        {rows.length === 0 && <p className="muted">No messages yet.</p>}
        {rows.map((m) => (
          <div key={m.id} className={`history-msg ${m.role}`}>
            <div className="history-meta">
              <span className="pill sm">{m.role === "assistant" ? "S.U.K.U" : m.role}</span>
              {m.intent && <span className="muted small">{m.intent}</span>}
              <span className="muted small">{new Date(m.created_at).toLocaleString()}</span>
            </div>
            <p className="history-content">{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
