import { useCallback, useEffect, useState } from "react";

const KEY = "pmo.display_name";

export function useDisplayName(): [string, (n: string) => void] {
  const [name, setName] = useState<string>(() => {
    try {
      return localStorage.getItem(KEY) ?? "Brett Anderson";
    } catch {
      return "Brett Anderson";
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(KEY, name);
    } catch {
      /* ignore */
    }
  }, [name]);

  const update = useCallback((n: string) => {
    setName(n.trim() || "Anonymous");
  }, []);

  return [name, update];
}
