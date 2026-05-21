export function speak(text: string, rate = 1) {
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = Math.min(2, Math.max(0.5, rate));
  window.speechSynthesis.speak(u);
}

export function getRecognitionCtor(): (new () => SpeechRecognition) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

/**
 * One-shot speech recognition. Chrome sometimes fires onend before/on top of onresult;
 * we delay the "no speech" reject so final results can still land. Also uses resultIndex
 * + isFinal (required when interimResults is true).
 */
export function listenOnce(): Promise<string> {
  const Ctor = getRecognitionCtor();
  if (!Ctor) {
    return Promise.reject(new Error("Speech recognition is not supported in this browser."));
  }

  const rec = new Ctor();
  const navLang = typeof navigator !== "undefined" ? navigator.language : "en-US";
  rec.lang = /^en/i.test(navLang) ? navLang : "en-US";
  rec.interimResults = true;
  rec.maxAlternatives = 1;
  rec.continuous = false;

  return new Promise((resolve, reject) => {
    let settled = false;
    let listenTimer: ReturnType<typeof window.setTimeout> | undefined;
    let endRejectTimer: ReturnType<typeof window.setTimeout> | undefined;

    const clearTimers = () => {
      if (listenTimer !== undefined) {
        window.clearTimeout(listenTimer);
        listenTimer = undefined;
      }
      if (endRejectTimer !== undefined) {
        window.clearTimeout(endRejectTimer);
        endRejectTimer = undefined;
      }
    };

    const detach = () => {
      try {
        rec.onresult = null;
        rec.onerror = null;
        rec.onend = null;
      } catch {
        /* ignore */
      }
    };

    const finish = (fn: () => void) => {
      if (settled) return;
      settled = true;
      clearTimers();
      detach();
      fn();
    };

    rec.onresult = (event: SpeechRecognitionEvent) => {
      let text = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const row = event.results[i];
        if (row.isFinal) {
          text += row[0]?.transcript ?? "";
        }
      }
      text = text.trim();
      if (text) {
        finish(() => resolve(text));
      }
    };

    rec.onerror = (ev: SpeechRecognitionErrorEvent) => {
      if (settled) return;
      if (ev.error === "aborted") return;
      const msg =
        ev.error === "not-allowed"
          ? "Microphone blocked. Click the lock icon in the address bar and allow the microphone for this site."
          : ev.error === "no-speech"
            ? "No speech heard. Wait for Listening, then speak clearly; reduce background noise."
            : ev.error === "audio-capture"
              ? "No microphone found or it is in use by another app."
              : ev.error === "network"
                ? "Speech recognition needs a network connection in Chrome. Check your connection."
                : `Speech recognition error: ${ev.error || "unknown"}.`;
      finish(() => reject(new Error(msg)));
    };

    rec.onend = () => {
      if (settled) return;
      // Let a late final onresult win (common Chrome ordering quirk).
      endRejectTimer = window.setTimeout(() => {
        endRejectTimer = undefined;
        finish(() =>
          reject(
            new Error(
              "No speech captured. Click the mic again, wait until it says Listening, then speak. If the browser asked for the microphone, choose Allow.",
            ),
          ),
        );
      }, 400);
    };

    listenTimer = window.setTimeout(() => {
      listenTimer = undefined;
      try {
        rec.stop();
      } catch {
        try {
          rec.abort();
        } catch {
          /* ignore */
        }
      }
      finish(() =>
        reject(new Error("Listening timed out after 30 seconds. Try again when you are ready to speak.")),
      );
    }, 30000);

    try {
      window.speechSynthesis.cancel();
      rec.start();
    } catch {
      finish(() =>
        reject(
          new Error(
            "Could not start the microphone. Reload the page, allow mic access, and make sure no other tab is listening.",
          ),
        ),
      );
    }
  });
}
