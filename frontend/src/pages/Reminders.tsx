import { useCallback, useEffect, useState } from "react";
import { dismissReminder, getReminders, type ReminderRow } from "../api";

export function Reminders() {
  const [rows, setRows] = useState<ReminderRow[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await getReminders());
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onDismiss(id: number) {
    try {
      await dismissReminder(id);
      await load();
    } catch {
      setErr("Could not dismiss reminder");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Reminders</h1>
        <p className="muted">
          Say or type: set a reminder or alarm at 10:00 AM, remind me to call at 3 PM, or list reminders / alarms.
        </p>
      </header>

      {err && <p className="error">{err}</p>}

      <div className="card">
        <div className="row-between" style={{ marginBottom: "0.75rem" }}>
          <h2 className="h2" style={{ margin: 0 }}>
            Upcoming ({rows.length})
          </h2>
          <button type="button" className="btn ghost sm" onClick={() => void load()}>
            Refresh
          </button>
        </div>
        {rows.length === 0 && <p className="muted">No upcoming reminders.</p>}
        <ul className="track-list">
          {rows.map((r) => (
            <li key={r.id} className="track-row">
              <div>
                <div className="track-title">{r.label}</div>
                <div className="muted small">
                  {new Date(r.fire_at).toLocaleString()}
                </div>
              </div>
              <button type="button" className="btn ghost sm danger" onClick={() => void onDismiss(r.id)}>
                Dismiss
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
