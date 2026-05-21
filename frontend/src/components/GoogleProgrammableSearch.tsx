import { useEffect, useRef } from "react";

type Props = { cx: string };

/**
 * Loads Google's hosted Programmable Search box (cse.js + .gcse-search).
 * cx is public (it appears in the embed URL); the API key stays on the server only.
 */
export function GoogleProgrammableSearch({ cx }: Props) {
  const inserted = useRef(false);

  useEffect(() => {
    if (!cx || inserted.current) return;
    const marker = `data-suku-cse="${cx}"`;
    if (document.querySelector(`script[${marker}]`)) {
      inserted.current = true;
      return;
    }
    const script = document.createElement("script");
    script.src = `https://cse.google.com/cse.js?cx=${encodeURIComponent(cx)}`;
    script.async = true;
    script.setAttribute("data-suku-cse", cx);
    document.body.appendChild(script);
    inserted.current = true;
  }, [cx]);

  if (!cx) {
    return <p className="muted small">Set VITE_GOOGLE_CSE_ID in frontend/.env (your Search engine ID).</p>;
  }

  return <div className="gcse-search" />;
}
