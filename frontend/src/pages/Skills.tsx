import { useEffect, useState } from "react";
import { getSkills, patchSkill, type SkillOut } from "../api";

export function Skills() {
  const [skills, setSkills] = useState<SkillOut[]>([]);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      setSkills(await getSkills());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function toggle(s: SkillOut) {
    try {
      const u = await patchSkill(s.id, !s.enabled);
      setSkills((prev) => prev.map((x) => (x.id === u.id ? u : x)));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Update failed");
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Skills</h1>
        <p className="muted">Enable or disable skills (stored in the database).</p>
      </header>

      {err && <p className="error">{err}</p>}

      <div className="skill-grid">
        {skills.map((s) => (
          <div key={s.id} className="card skill-card">
            <div className="skill-head">
              <h2 className="h2">{s.name}</h2>
              <button
                type="button"
                className={s.enabled ? "btn primary sm" : "btn ghost sm"}
                onClick={() => void toggle(s)}
              >
                {s.enabled ? "On" : "Off"}
              </button>
            </div>
            <p className="muted small">{s.description}</p>
            <code className="code">{s.id}</code>
          </div>
        ))}
      </div>
    </div>
  );
}
