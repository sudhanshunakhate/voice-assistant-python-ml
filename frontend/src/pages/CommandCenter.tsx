import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  clearHistory,
  getHistory,
  getSettings,
  getSystemStats,
  postCommand,
  type CommandOut,
  type MessageRow,
  type SystemStats,
} from "../api";
import { getRecognitionCtor, listenOnce, speak } from "../voice";
import { useMusicPlayer } from "../context/MusicPlayerContext";
import {
  closeTabIfOpen,
  openYoutubeInPreparedTab,
  preOpenBlankTab,
  shouldPreopenYoutubeTabHint,
} from "../youtubeOpen";
import { SUKU_FULL_NAME } from "../branding";

type TranscriptItem = {
  id: string;
  role: "user" | "assistant";
  text: string;
  ts: Date;
};

function formatHeaderTime(d: Date) {
  const t = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  const day = d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  return `${t} | ${day}`;
}

function formatClock(d: Date) {
  return d.toLocaleTimeString(undefined, { hour12: false });
}

async function fetchOpenMeteo(city: string) {
  const g = await fetch(
    `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1`
  );
  const gj = (await g.json()) as { results?: { latitude: number; longitude: number; name: string }[] };
  if (!gj.results?.[0]) return null;
  const { latitude, longitude, name } = gj.results[0];
  const w = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`
  );
  const wj = (await w.json()) as {
    current_weather?: { temperature: number; weathercode: number };
  };
  if (!wj.current_weather) return null;
  return {
    name,
    temp: wj.current_weather.temperature,
    code: wj.current_weather.weathercode,
  };
}

export function CommandCenter() {
  const navigate = useNavigate();
  const cmdRef = useRef<HTMLTextAreaElement>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  const [headerTime, setHeaderTime] = useState(() => new Date());
  const [clock, setClock] = useState(() => new Date());
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [text, setText] = useState("");
  const [skipWake, setSkipWake] = useState(true);
  const [wakeWord, setWakeWord] = useState("hey suku");
  const [voiceRate, setVoiceRate] = useState(1);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [weather, setWeather] = useState<{ name: string; temp: number; code: number } | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherCity, setWeatherCity] = useState(() => localStorage.getItem("va_weather_city") || "London");
  const [youtubeBlockedUrl, setYoutubeBlockedUrl] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [messagePanelTab, setMessagePanelTab] = useState<"live" | "history">("live");
  const [historyRows, setHistoryRows] = useState<MessageRow[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const { playTrackId, playNext, playPrevious, pause, stop, refresh, current, playing, toggle } =
    useMusicPlayer();
  const speechOk = !!getRecognitionCtor();

  const applyPlaybackAction = useCallback(
    async (out: CommandOut, preTab: Window | null = null) => {
      const action = out.action;
      const payload = out.payload;
      if (action === "open_youtube" && payload && typeof payload.url === "string") {
        const ok = openYoutubeInPreparedTab(payload.url, preTab);
        setYoutubeBlockedUrl(ok ? null : payload.url);
        return;
      }
      closeTabIfOpen(preTab);
      setYoutubeBlockedUrl(null);
      if (action === "play_track" && payload && typeof payload.track_id === "number") {
        await refresh();
        playTrackId(payload.track_id);
      } else if (action === "next") playNext();
      else if (action === "previous") playPrevious();
      else if (action === "pause") pause();
      else if (action === "stop") stop();
    },
    [playTrackId, playNext, playPrevious, pause, stop, refresh]
  );

  const refreshHistoryPanel = useCallback(async () => {
    setHistoryLoading(true);
    try {
      setHistoryRows(await getHistory());
    } catch {
      setHistoryRows([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const runCommand = useCallback(
    async (raw: string, opts?: { silent?: boolean; preTab?: Window | null }) => {
      const t = raw.trim();
      if (!t) return;
      const preTab = opts?.preTab ?? null;
      setErr(null);
      const userLine: TranscriptItem = {
        id: `u-${Date.now()}`,
        role: "user",
        text: t,
        ts: new Date(),
      };
      if (!opts?.silent) setTranscript((prev) => [...prev, userLine]);
      setBusy(true);
      try {
        const out = await postCommand(t, skipWake);
        const botLine: TranscriptItem = {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: out.response,
          ts: new Date(),
        };
        if (!opts?.silent) setTranscript((prev) => [...prev, botLine]);
        speak(out.response, 0.5 + voiceRate * 0.5);
        await applyPlaybackAction(out, preTab);
      } catch (e) {
        closeTabIfOpen(preTab);
        setErr(e instanceof Error ? e.message : "Request failed");
        if (!opts?.silent) {
          setTranscript((prev) => [
            ...prev,
            {
              id: `e-${Date.now()}`,
              role: "assistant",
              text: "Sorry, something went wrong.",
              ts: new Date(),
            },
          ]);
        }
      } finally {
        setBusy(false);
        void refreshHistoryPanel();
      }
    },
    [skipWake, voiceRate, applyPlaybackAction, refreshHistoryPanel]
  );

  useEffect(() => {
    const id = setInterval(() => {
      const n = new Date();
      setHeaderTime(n);
      setClock(n);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    getSettings()
      .then((s) => {
        setWakeWord(s.wake_word);
        setVoiceRate(s.voice_rate || 1);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    void refreshHistoryPanel();
  }, [refreshHistoryPanel]);

  useEffect(() => {
    if (messagePanelTab === "history") void refreshHistoryPanel();
  }, [messagePanelTab, refreshHistoryPanel]);

  useEffect(() => {
    const tick = () => {
      getSystemStats().then(setStats).catch(() => setStats(null));
    };
    tick();
    const id = setInterval(tick, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  async function onSend() {
    const t = text.trim();
    if (!t || busy) return;
    const preTab = shouldPreopenYoutubeTabHint(t) ? preOpenBlankTab() : null;
    setText("");
    setMessagePanelTab("live");
    setTranscript([]);
    await runCommand(t, { preTab });
  }

  async function onMic() {
    if (!speechOk || listening || busy) return;
    // Do not pre-open a blank tab here: window.open on the same gesture as the mic
    // steals focus and breaks Web Speech API recognition in Chrome/Edge.
    setMessagePanelTab("live");
    setTranscript([]);
    setListening(true);
    setErr(null);
    try {
      const heard = await listenOnce();
      setTranscript((prev) => [
        ...prev,
        { id: `u-${Date.now()}`, role: "user", text: heard, ts: new Date() },
      ]);
      setBusy(true);
      const out = await postCommand(heard, skipWake);
      setTranscript((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", text: out.response, ts: new Date() },
      ]);
      speak(out.response, 0.5 + voiceRate * 0.5);
      await applyPlaybackAction(out, null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Listen failed");
    } finally {
      setListening(false);
      setBusy(false);
      void refreshHistoryPanel();
    }
  }

  async function onClearTranscript() {
    if (transcript.length === 0 && !youtubeBlockedUrl && historyRows.length === 0) return;
    if (!confirm("Delete all conversation history on the server and clear the live transcript?")) return;
    setClearing(true);
    setErr(null);
    try {
      await clearHistory();
      setTranscript([]);
      setYoutubeBlockedUrl(null);
      await refreshHistoryPanel();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not clear history");
    } finally {
      setClearing(false);
    }
  }

  async function loadWeather() {
    setWeatherLoading(true);
    setErr(null);
    try {
      localStorage.setItem("va_weather_city", weatherCity);
      const w = await fetchOpenMeteo(weatherCity);
      setWeather(w);
      if (!w) setErr("City not found.");
    } catch {
      setErr("Weather unavailable.");
      setWeather(null);
    } finally {
      setWeatherLoading(false);
    }
  }

  return (
    <div className="cc-root">
      <header className="cc-topbar">
        <div className="cc-topbar-left">
          <span className="cc-mic-icon" aria-hidden>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <rect x="9" y="3" width="6" height="11" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0" strokeLinecap="round" />
              <path d="M12 18v3M8 21h8" strokeLinecap="round" />
            </svg>
          </span>
          <div>
            <div className="cc-title">S.U.K.U</div>
            <div className="cc-suku-full">{SUKU_FULL_NAME}</div>
            <div className="cc-subtitle">Voice command system</div>
          </div>
        </div>
        <div className="cc-topbar-time">{formatHeaderTime(headerTime)}</div>
      </header>

      <div className="cc-grid">
        <section className="cc-panel cc-voice-panel">
          <div className="cc-panel-head">
            <span className="cc-panel-title">VOICE COMMANDS</span>
            <span className="cc-status">
              <span className="cc-status-dots" />
              S.U.K.U ACTIVE
            </span>
          </div>

          <div className="cc-listen-block">
            <button
              type="button"
              className={`cc-mic-ring ${listening ? "listening" : ""}`}
              onClick={() => void onMic()}
              disabled={!speechOk || busy}
              title={speechOk ? "Tap to speak" : "Speech recognition not supported"}
            >
              <span className="cc-mic-inner">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 14c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v5c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              </span>
            </button>
            <div>
              <div className="cc-listen-label">{listening ? "LISTENING…" : "READY"}</div>
              <div className="cc-wave" aria-hidden>
                {[...Array(12)].map((_, i) => (
                  <span key={i} className={listening ? "active" : ""} style={{ animationDelay: `${i * 0.08}s` }} />
                ))}
              </div>
            </div>
          </div>

          <label className="cc-check">
            <input
              type="checkbox"
              checked={skipWake}
              onChange={(e) => setSkipWake(e.target.checked)}
            />
            Skip wake word ({wakeWord})
          </label>

          <div className="cc-cmd-box">
            <textarea
              ref={cmdRef}
              className="cc-textarea"
              rows={2}
              placeholder="Try: play music Despacito — play Bohemian Rhapsody — what time is it…"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) void onSend();
              }}
            />
            <div className="cc-cmd-actions">
              <button type="button" className="cc-btn cc-btn-primary" disabled={busy} onClick={() => void onSend()}>
                {busy ? "Processing…" : "Execute"}
              </button>
              <span className="cc-hint">Ctrl+Enter</span>
            </div>
          </div>

          {err && <p className="cc-error">{err}</p>}
          {youtubeBlockedUrl && (
            <p className="cc-error">
              Could not open YouTube.{" "}
              <a href={youtubeBlockedUrl} target="_blank" rel="noopener noreferrer">
                Open this link
              </a>
            </p>
          )}

          <div className="cc-transcript-head-row">
            <div className="cc-transcript-head">Messages</div>
            <button
              type="button"
              className="cc-btn cc-btn-clear"
              disabled={clearing || (transcript.length === 0 && !youtubeBlockedUrl && historyRows.length === 0)}
              onClick={() => void onClearTranscript()}
            >
              {clearing ? "Clearing…" : "Clear all"}
            </button>
          </div>
          <div className="cc-transcript-tabs" role="tablist" aria-label="Message view">
            <button
              type="button"
              role="tab"
              aria-selected={messagePanelTab === "live"}
              className={`cc-transcript-tab ${messagePanelTab === "live" ? "active" : ""}`}
              onClick={() => setMessagePanelTab("live")}
            >
              Live
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={messagePanelTab === "history"}
              className={`cc-transcript-tab ${messagePanelTab === "history" ? "active" : ""}`}
              onClick={() => setMessagePanelTab("history")}
            >
              History
            </button>
          </div>
          <p className="cc-transcript-hint">
            {messagePanelTab === "live"
              ? "Each new Execute or mic tap starts a fresh live view. Everything is still saved under History."
              : "All turns stored in SQLite (same as the History page)."}
          </p>
          <div className="cc-transcript">
            {messagePanelTab === "live" ? (
              <>
                {transcript.length === 0 && (
                  <p className="cc-empty">No live messages yet — run a command or tap the mic.</p>
                )}
                {transcript.map((line) => (
                  <div key={line.id} className={`cc-msg ${line.role}`}>
                    <div className="cc-msg-head">
                      <span>{line.role === "user" ? "User" : "S.U.K.U"}</span>
                      <time>{line.ts.toLocaleTimeString(undefined, { hour12: false })}</time>
                    </div>
                    <p>{line.text}</p>
                  </div>
                ))}
                <div ref={transcriptEndRef} />
              </>
            ) : (
              <>
                {historyLoading && <p className="cc-empty">Loading…</p>}
                {!historyLoading && historyRows.length === 0 && (
                  <p className="cc-empty">No messages yet.</p>
                )}
                {!historyLoading &&
                  historyRows.map((m) => (
                    <div key={m.id} className={`cc-msg ${m.role === "user" ? "user" : "assistant"}`}>
                      <div className="cc-msg-head">
                        <span>{m.role === "user" ? "User" : "S.U.K.U"}</span>
                        <time>{new Date(m.created_at).toLocaleTimeString(undefined, { hour12: false })}</time>
                      </div>
                      {m.intent && <span className="cc-msg-intent">{m.intent}</span>}
                      <p>{m.content}</p>
                    </div>
                  ))}
              </>
            )}
          </div>
        </section>

        <div className="cc-right-col">
          <section className="cc-panel cc-stats-panel">
            <div className="cc-mini-grid">
              <div className="cc-stat-card">
                <div className="cc-stat-label">Memory</div>
                <div className="cc-stat-value">
                  {stats ? `${stats.memory_percent}%` : "—"}
                </div>
                <div className="cc-stat-sub">
                  {stats && stats.memory_total_gb ? `/ ${stats.memory_total_gb} GB total` : " "}
                </div>
              </div>
              <div className="cc-stat-card">
                <div className="cc-stat-label">CPU</div>
                <div className="cc-stat-value">{stats ? `${stats.cpu_percent}%` : "—"}</div>
                <div className="cc-stat-sub">Usage</div>
              </div>
              <div className="cc-stat-card cc-stat-wide">
                <div className="cc-stat-label">Network</div>
                <div className="cc-stat-value sm">{stats?.network ?? "—"}</div>
              </div>
            </div>
            <div className="cc-clock-card">
              <div className="cc-clock-label">Current time</div>
              <div className="cc-clock-digital">{formatClock(clock)}</div>
              <div className="cc-clock-date">
                {clock.toLocaleDateString(undefined, {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
          </section>

          <section className="cc-panel cc-tiles-panel">
            <div className="cc-panel-head">
              <span className="cc-panel-title">Skills &amp; integrations</span>
            </div>
            <div className="cc-tiles">
              <button
                type="button"
                className="cc-tile glow"
                onClick={() => navigate("/music")}
              >
                <span className="cc-tile-icon">♪</span>
                Music &amp; YouTube
              </button>
              <button
                type="button"
                className="cc-tile"
                onClick={() => {
                  setMessagePanelTab("live");
                  setTranscript([]);
                  void runCommand("what time is it");
                }}
              >
                <span className="cc-tile-icon">◷</span>
                Time &amp; Date
              </button>
              <button type="button" className="cc-tile" onClick={() => void loadWeather()}>
                <span className="cc-tile-icon">☁</span>
                Weather Info
              </button>
              <button type="button" className="cc-tile" onClick={() => navigate("/skills")}>
                <span className="cc-tile-icon">⌘</span>
                System Control
              </button>
              <button type="button" className="cc-tile" onClick={() => navigate("/search")}>
                <span className="cc-tile-icon">⌕</span>
                Web Search
              </button>
              <button
                type="button"
                className="cc-tile glow"
                onClick={() => navigate("/settings")}
              >
                <span className="cc-tile-icon">⚙</span>
                Settings
              </button>
            </div>
            <div className="cc-weather-bar">
              <input
                className="cc-weather-input"
                value={weatherCity}
                onChange={(e) => setWeatherCity(e.target.value)}
                placeholder="City for weather"
              />
              <button type="button" className="cc-btn cc-btn-ghost" onClick={() => void loadWeather()} disabled={weatherLoading}>
                {weatherLoading ? "…" : "Refresh weather"}
              </button>
            </div>
            {weather && (
              <div className="cc-weather-result">
                <strong>{weather.name}</strong> — {weather.temp}°C (code {weather.code})
              </div>
            )}
          </section>
        </div>
      </div>

      <div className="cc-dock">
        <div className="cc-dock-links">
          <Link to="/reminders">Reminders</Link>
          <Link to="/history">History</Link>
          <Link to="/music">Music &amp; YouTube</Link>
          <Link to="/voice">Voice</Link>
          <Link to="/skills">Skills</Link>
          <Link to="/settings">Settings</Link>
          <Link to="/search">Search</Link>
        </div>
        {current && (
          <div className="cc-now-playing">
            <span>
              ♪ {current.title} — {playing ? "playing" : "paused"}
            </span>
            <button type="button" className="cc-btn cc-btn-ghost sm" onClick={toggle}>
              {playing ? "Pause" : "Play"}
            </button>
          </div>
        )}
        <div className="cc-badges">
          <span className="cc-badge">Python</span>
          <span className="cc-badge cc-badge-ai">AI / ML</span>
        </div>
      </div>
    </div>
  );
}
