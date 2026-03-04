import { createContext, useCallback, useContext, useState } from "react";

export type ToastLevel = "success" | "warn" | "error" | "info";
type ToastItem = { id: number; msg: string; level: ToastLevel };
type ToastCtx = { add: (msg: string, level?: ToastLevel) => void };

const Ctx = createContext<ToastCtx>({ add: () => {} });
let _id = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const add = useCallback((msg: string, level: ToastLevel = "info") => {
    const id = ++_id;
    setItems((t) => [...t, { id, msg, level }]);
    setTimeout(() => setItems((t) => t.filter((x) => x.id !== id)), 3800);
  }, []);

  const remove = (id: number) => setItems((t) => t.filter((x) => x.id !== id));

  return (
    <Ctx.Provider value={{ add }}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`toast toast--${t.level}`} onClick={() => remove(t.id)}>
            <span className="toast__icon">
              {t.level === "success" ? "✓" : t.level === "error" ? "✗" : t.level === "warn" ? "⚠" : "ℹ"}
            </span>
            <span className="toast__msg">{t.msg}</span>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast() {
  const { add } = useContext(Ctx);
  return {
    success: (msg: string) => add(msg, "success"),
    warn: (msg: string) => add(msg, "warn"),
    error: (msg: string) => add(msg, "error"),
    info: (msg: string) => add(msg, "info"),
  };
}
