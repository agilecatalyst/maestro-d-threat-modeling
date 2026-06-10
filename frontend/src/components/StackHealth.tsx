import { useEffect, useState } from "react";
import { getApiHealth } from "../api/client";

export function StackHealth() {
  const [status, setStatus] = useState<"ok" | "down" | "checking">("checking");

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const health = await getApiHealth();
        if (!cancelled) setStatus(health.status === "healthy" ? "ok" : "down");
      } catch {
        if (!cancelled) setStatus("down");
      }
    };
    void check();
    const timer = window.setInterval(() => void check(), 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const label =
    status === "checking" ? "API…" : status === "ok" ? "API online" : "API offline";
  const color = status === "ok" ? "var(--accent)" : status === "down" ? "#e57373" : "var(--text-muted)";

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: color,
          display: "inline-block",
        }}
      />
      {label}
    </span>
  );
}
