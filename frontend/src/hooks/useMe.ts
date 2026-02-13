import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Me } from "../api/types";

export function useMe() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api
      .get<Me>("/api/me")
      .then((u) => {
        if (!alive) return;
        setMe(u);
      })
      .catch(() => {
        if (!alive) return;
        setMe(null);
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return { me, setMe, loading };
}

