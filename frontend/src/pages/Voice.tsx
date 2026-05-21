import { useEffect, useState } from "react";
import { getSettings, postCommand, type CommandOut } from "../api";
import { getRecognitionCtor, listenOnce, speak } from "../voice";
import { useMusicPlayer } from "../context/MusicPlayerContext";
import { closeTabIfOpen, openYoutubeInPreparedTab } from "../youtubeOpen";

export function Voice() {
  const [skipWake, setSkipWake] = useState(false);
  const [wakeWord, setWakeWord] = useState("hey suku");
  const [voiceRate, setVoiceRate] = useState(1);
  const [transcript, setTranscript] = useState("");
  const [last, setLast] = useState<CommandOut | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const [youtubeBlockedUrl, setYoutubeBlockedUrl] = useState<string | null>(null);
  const { playTrackId, playNext, playPrevious, pause, stop, refresh } = useMusicPlayer();

  const supported = !!getRecognitionCtor();

  useEffect(() => {
    getSettings()
      .then((s) => {
        setWakeWord(s.wake_word);
        setVoiceRate(s.voice_rate || 1);
      })
      .catch(() => {});
  }, []);

  async function runCommand(text: string, preTab: Window | null = null) {
    setErr(null);
    try {
      const out = await postCommand(text, skipWake);
      setLast(out);
      speak(out.response, 0.5 + voiceRate * 0.5);

      const action = out.action;
      const payload = out.payload;
      if (action === "open_youtube" && payload && typeof payload.url === "string") {
        const ok = openYoutubeInPreparedTab(payload.url, preTab);
        setYoutubeBlockedUrl(ok ? null : payload.url);
      } else {
        closeTabIfOpen(preTab);
        setYoutubeBlockedUrl(null);
      }
      if (action === "play_track" && payload && typeof payload.track_id === "number") {
        await refresh();
        playTrackId(payload.track_id);
      } else if (action === "next") {
        playNext();
      } else if (action === "previous") {
        playPrevious();
      } else if (action === "pause") {
        pause();
      } else if (action === "stop") {
        stop();
      }
    } catch (e) {
      closeTabIfOpen(preTab);
      setErr(e instanceof Error ? e.message : "Request failed");
    }
  }

  async function listenOnceClick() {
    if (!supported) return;
    setListening(true);
    setErr(null);
    try {
      const t = await listenOnce();
      setTranscript(t);
      await runCommand(t, null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Listen failed");
    } finally {
      setListening(false);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Voice</h1>
        <p className="muted">Use your microphone (Chrome or Edge recommended).</p>
      </header>

      {!supported && (
        <div className="card error-banner">Speech recognition is not available in this browser.</div>
      )}

      <div className="card">
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={skipWake}
            onChange={(e) => setSkipWake(e.target.checked)}
          />
          <span>Skip wake word ({wakeWord})</span>
        </label>
      </div>

      <div className="card voice-card">
        <button
          type="button"
          className="btn primary large mic-btn"
          disabled={!supported || listening}
          onClick={() => void listenOnceClick()}
        >
          {listening ? "Listening…" : "Tap to speak"}
        </button>
        {transcript && (
          <p className="transcript">
            <span className="muted">You said:</span> {transcript}
          </p>
        )}
        {err && <p className="error">{err}</p>}
        {youtubeBlockedUrl && (
          <p className="error">
            Could not open YouTube.{" "}
            <a href={youtubeBlockedUrl} target="_blank" rel="noopener noreferrer">
              Open this link
            </a>
          </p>
        )}
      </div>

      {last && (
        <div className="card response-card">
          <div className="pill">{last.intent}</div>
          <p className="response-text">{last.response}</p>
        </div>
      )}
    </div>
  );
}
