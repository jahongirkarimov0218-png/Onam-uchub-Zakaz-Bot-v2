import { useEffect, useState } from "react";

function normalize(raw: string): string {
  const h = raw.replace(/^#/, "");
  return h === "" ? "/" : h;
}

/** Tiny hash router hook: re-renders on hashchange, no route table baked in
 * (each app parses its own path shape from the returned string). */
export function useHashRoute(): string {
  const [hash, setHash] = useState(() =>
    typeof window !== "undefined" ? normalize(window.location.hash) : "/"
  );
  useEffect(() => {
    const onChange = () => setHash(normalize(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export function navigate(path: string): void {
  window.location.hash = path;
}
