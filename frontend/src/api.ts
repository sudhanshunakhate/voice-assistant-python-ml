export type CommandOut = {
  response: string;
  intent: string;
  action?: string | null;
  payload?: Record<string, unknown> | null;
};

export type MessageRow = {
  id: number;
  role: string;
  content: string;
  intent: string | null;
  created_at: string;
};

export type SettingsOut = {
  wake_word: string;
  voice_rate: number;
  items: { key: string; value: string }[];
};

export type SkillOut = {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
};

export type MusicTrack = {
  id: number;
  title: string;
  artist: string;
  file_name: string;
  url: string;
  duration_seconds: number | null;
  created_at: string;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}

export function postCommand(text: string, skipWake: boolean) {
  return api<CommandOut>("/api/assistant/command", {
    method: "POST",
    body: JSON.stringify({ text, skip_wake_check: skipWake }),
  });
}

export function getHistory() {
  return api<MessageRow[]>("/api/history");
}

export function clearHistory() {
  return api<{ ok: boolean }>("/api/history", { method: "DELETE" });
}

export function getSettings() {
  return api<SettingsOut>("/api/settings");
}

export function putSettings(body: { wake_word?: string; voice_rate?: number }) {
  return api<SettingsOut>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function getSkills() {
  return api<SkillOut[]>("/api/skills");
}

export function patchSkill(id: string, enabled: boolean) {
  return api<SkillOut>(`/api/skills/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  });
}

export function getTracks() {
  return api<MusicTrack[]>("/api/music/tracks");
}

export function deleteTrack(id: number) {
  return api<{ ok: boolean }>(`/api/music/tracks/${id}`, { method: "DELETE" });
}

export function uploadTrack(file: File, title?: string, artist?: string) {
  const fd = new FormData();
  fd.append("file", file);
  if (title) fd.append("title", title);
  if (artist) fd.append("artist", artist);
  return fetch("/api/music/tracks", { method: "POST", body: fd }).then((r) => {
    if (!r.ok) return r.text().then((t) => Promise.reject(new Error(t)));
    return r.json() as Promise<MusicTrack>;
  });
}

export function streamUrl(trackId: number) {
  return `/api/music/stream/${trackId}`;
}

export type ReminderRow = {
  id: number;
  label: string;
  fire_at: string;
  dismissed: boolean;
  created_at: string;
};

export function getReminders() {
  return api<ReminderRow[]>("/api/reminders");
}

export function dismissReminder(id: number) {
  return fetch(`/api/reminders/${id}`, { method: "DELETE" }).then((r) => {
    if (!r.ok) return r.text().then((t) => Promise.reject(new Error(t)));
    return r.json() as Promise<{ ok: boolean }>;
  });
}

export type SystemStats = {
  memory_percent: number;
  memory_total_gb: number;
  cpu_percent: number;
  network: string;
  detail?: boolean;
};

export function getSystemStats() {
  return api<SystemStats>("/api/system/stats");
}

export type YoutubeHit = {
  id: string;
  title: string;
  url: string;
  duration?: string;
};

export function searchYoutube(q: string, limit = 8) {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return api<YoutubeHit[]>(`/api/youtube/search?${params}`);
}

export function getSearchAnswer(q: string) {
  const params = new URLSearchParams({ q });
  return api<{ answer: string }>(`/api/search/answer?${params}`);
}

export function getSearchStatus() {
  return api<{ google_custom_search_configured: boolean }>("/api/search/status");
}
