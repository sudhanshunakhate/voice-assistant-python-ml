import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { getTracks, streamUrl, type MusicTrack } from "../api";

type Ctx = {
  tracks: MusicTrack[];
  currentIndex: number;
  current: MusicTrack | null;
  playing: boolean;
  refresh: () => Promise<void>;
  playTrackId: (id: number) => void;
  playNext: () => void;
  playPrevious: () => void;
  pause: () => void;
  stop: () => void;
  toggle: () => void;
  audioRef: React.RefObject<HTMLAudioElement>;
};

const MusicPlayerContext = createContext<Ctx | null>(null);

export function MusicPlayerProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [tracks, setTracks] = useState<MusicTrack[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  const refresh = useCallback(async () => {
    const list = await getTracks();
    setTracks(list);
  }, []);

  useEffect(() => {
    refresh().catch(() => {});
  }, [refresh]);

  const current = tracks[currentIndex] ?? null;

  const playIndex = useCallback(
    (idx: number) => {
      if (!tracks.length) return;
      const i = ((idx % tracks.length) + tracks.length) % tracks.length;
      setCurrentIndex(i);
      const el = audioRef.current;
      if (el) {
        el.src = streamUrl(tracks[i].id);
        el.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
      }
    },
    [tracks]
  );

  const playTrackId = useCallback(
    (id: number) => {
      const idx = tracks.findIndex((t) => t.id === id);
      if (idx >= 0) playIndex(idx);
    },
    [tracks, playIndex]
  );

  const playNext = useCallback(() => playIndex(currentIndex + 1), [playIndex, currentIndex]);
  const playPrevious = useCallback(() => playIndex(currentIndex - 1), [playIndex, currentIndex]);

  const pause = useCallback(() => {
    audioRef.current?.pause();
    setPlaying(false);
  }, []);

  const stop = useCallback(() => {
    const el = audioRef.current;
    if (el) {
      el.pause();
      el.currentTime = 0;
    }
    setPlaying(false);
  }, []);

  const toggle = useCallback(() => {
    const el = audioRef.current;
    if (!el?.src) return;
    if (playing) {
      el.pause();
      setPlaying(false);
    } else {
      el.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
    }
  }, [playing]);

  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    const onEnded = () => {
      setPlaying(false);
      playNext();
    };
    el.addEventListener("ended", onEnded);
    return () => el.removeEventListener("ended", onEnded);
  }, [playNext]);

  const value: Ctx = {
    tracks,
    currentIndex,
    current,
    playing,
    refresh,
    playTrackId,
    playNext,
    playPrevious,
    pause,
    stop,
    toggle,
    audioRef,
  };

  return (
    <MusicPlayerContext.Provider value={value}>
      <audio ref={audioRef} style={{ display: "none" }} />
      {children}
    </MusicPlayerContext.Provider>
  );
}

export function useMusicPlayer() {
  const c = useContext(MusicPlayerContext);
  if (!c) throw new Error("useMusicPlayer outside provider");
  return c;
}
