/**
 * YouTube opens in a new tab (embed is often blocked by video owners).
 * Pre-open about:blank in the same user gesture as typed Execute (when the hint matches),
 * then assign the URL after the API returns — avoids popup blockers.
 * Do not use noopener on the blank tab or the opener cannot navigate it.
 *
 * Do not pre-open on the mic button: opening a tab in that gesture steals focus and
 * breaks Web Speech API recognition. When a new tab is blocked (e.g. after voice),
 * we fall back to navigating this tab to YouTube so no extra click is needed.
 */

export function preOpenBlankTab(): Window | null {
  try {
    return window.open("about:blank", "_blank");
  } catch {
    return null;
  }
}

export function closeTabIfOpen(w: Window | null): void {
  if (!w || w.closed) return;
  try {
    w.close();
  } catch {
    /* ignore */
  }
}

function navigatePreparedTab(w: Window, url: string): boolean {
  try {
    w.location.assign(url);
    try {
      w.focus();
    } catch {
      /* ignore */
    }
    return true;
  } catch {
    /* continue */
  }
  try {
    w.location.replace(url);
    try {
      w.focus();
    } catch {
      /* ignore */
    }
    return true;
  } catch {
    /* continue */
  }
  try {
    w.location.href = url;
    try {
      w.focus();
    } catch {
      /* ignore */
    }
    return true;
  } catch {
    return false;
  }
}

export function openYoutubeInPreparedTab(url: string, preOpened: Window | null): boolean {
  if (preOpened && !preOpened.closed) {
    if (navigatePreparedTab(preOpened, url)) {
      return true;
    }
    closeTabIfOpen(preOpened);
  }
  // No "noopener" in the feature string: with noopener many browsers return null even when a tab opened,
  // which would make us wrongly fall back to same-tab navigation.
  const w = window.open(url, "_blank");
  try {
    w?.focus();
  } catch {
    /* ignore */
  }
  if (w && !w.closed) {
    return true;
  }
  try {
    window.location.assign(url);
    return true;
  } catch {
    return false;
  }
}

export function tryOpenYoutubeTab(url: string): boolean {
  return openYoutubeInPreparedTab(url, null);
}

export function shouldPreopenYoutubeTabHint(text: string): boolean {
  const t = text.toLowerCase();
  return (
    /\bplay\b/.test(t) ||
    /\byoutube\b/.test(t) ||
    /\bon\s+youtube\b/.test(t) ||
    /^\s*yt\s+\S/.test(t) ||
    /\bmusic\s+\S{3,}/.test(t) ||
    /\bplay\s+(the\s+)?(music|song)\s+(of|from)\b/.test(t) ||
    /\bplay\s+(me\s+)?(a\s+)?(song|track|music)\b/.test(t) ||
    /\blisten\s+to\b/.test(t)
  );
}
