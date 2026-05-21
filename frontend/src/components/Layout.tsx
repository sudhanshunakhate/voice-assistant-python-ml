import { Link, Outlet, useLocation } from "react-router-dom";
import { useMusicPlayer } from "../context/MusicPlayerContext";
import { SUKU_FULL_NAME } from "../branding";

export function Layout() {
  const loc = useLocation();
  const isHome = loc.pathname === "/";
  const { current, playing, toggle, playNext, playPrevious, stop } = useMusicPlayer();

  if (isHome) {
    return <Outlet />;
  }

  return (
    <div className="dark-app dark-app-sub">
      <header className="cc-topbar cc-topbar-sub">
        <div className="cc-topbar-left">
          <Link to="/" className="cc-back">
            ← Command center
          </Link>
          <span className="cc-topbar-sep" />
          <span className="cc-title-sm" title={`${SUKU_FULL_NAME} — voice assistant`}>
            S.U.K.U
          </span>
        </div>
        {current && (
          <div className="cc-sub-now">
            <span className="cc-sub-now-text">
              ♪ {current.title} ({playing ? "playing" : "paused"})
            </span>
            <button type="button" className="cc-btn cc-btn-ghost sm" onClick={toggle}>
              {playing ? "Pause" : "Play"}
            </button>
            <button type="button" className="cc-btn cc-btn-ghost sm" onClick={playPrevious}>
              Prev
            </button>
            <button type="button" className="cc-btn cc-btn-ghost sm" onClick={playNext}>
              Next
            </button>
            <button type="button" className="cc-btn cc-btn-ghost sm" onClick={stop}>
              Stop
            </button>
          </div>
        )}
      </header>
      <main className="dark-page-main">
        <Outlet />
      </main>
    </div>
  );
}
