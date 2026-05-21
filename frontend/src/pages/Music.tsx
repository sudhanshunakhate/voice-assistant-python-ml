import { useState } from "react";
import { searchYoutube, type YoutubeHit } from "../api";
import { tryOpenYoutubeTab } from "../youtubeOpen";

export function Music() {
  const [ytQuery, setYtQuery] = useState("");
  const [ytResults, setYtResults] = useState<YoutubeHit[]>([]);
  const [ytBusy, setYtBusy] = useState(false);
  const [ytErr, setYtErr] = useState<string | null>(null);

  async function onYoutubeSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = ytQuery.trim();
    if (!q) return;
    setYtBusy(true);
    setYtErr(null);
    try {
      const hits = await searchYoutube(q, 10);
      setYtResults(hits);
      if (hits.length === 0) setYtErr("No videos found. Try different words.");
    } catch {
      setYtErr("Search failed. Is the API running?");
      setYtResults([]);
    } finally {
      setYtBusy(false);
    }
  }

  function openYoutube(hit: YoutubeHit) {
    tryOpenYoutubeTab(hit.url);
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Music &amp; YouTube</h1>
        <p className="muted">
          Say <strong>play music</strong> with a song name, or <strong>play</strong> followed by what you want — S.U.K.U
          searches YouTube and opens the top match in a <strong>new tab</strong>. You can also search below.
        </p>
      </header>

      <div className="card">
        <h2 className="h2">Search YouTube</h2>
        <p className="muted small" style={{ marginTop: 0 }}>
          Results open in a new browser tab (playback is on YouTube).
        </p>
        <form className="row" style={{ marginTop: "0.75rem", flexWrap: "wrap" }} onSubmit={(e) => void onYoutubeSearch(e)}>
          <input
            className="input"
            style={{ flex: "1 1 200px", minWidth: 180 }}
            placeholder="Song, artist, or video…"
            value={ytQuery}
            onChange={(e) => setYtQuery(e.target.value)}
          />
          <button type="submit" className="btn primary" disabled={ytBusy || !ytQuery.trim()}>
            {ytBusy ? "Searching…" : "Search"}
          </button>
        </form>
        {ytErr && <p className="error">{ytErr}</p>}
        {ytResults.length > 0 && (
          <ul className="track-list" style={{ marginTop: "0.75rem" }}>
            {ytResults.map((h) => (
              <li key={h.id} className="track-row">
                <div>
                  <div className="track-title">{h.title}</div>
                  {h.duration && <div className="muted small">{h.duration}</div>}
                </div>
                <button type="button" className="btn primary sm" onClick={() => openYoutube(h)}>
                  Open tab
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
