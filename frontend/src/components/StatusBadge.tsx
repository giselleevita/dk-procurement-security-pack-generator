const STATUS_ICON: Record<string, string> = {
  pass: "✓",
  warn: "⚠",
  fail: "✗",
  unknown: "–",
};

export function StatusBadge({ status, large }: { status: string; large?: boolean }) {
  const icon = STATUS_ICON[status] ?? "–";
  return (
    <span className={`badge badge--${status}${large ? " badge--lg" : ""}`} aria-label={status}>
      <span className="badge__icon">{icon}</span>
      <span className="badge__label">{status}</span>
    </span>
  );
}
