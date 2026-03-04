export function ScoreRing({
  pass,
  warn,
  fail,
  total,
}: {
  pass: number;
  warn: number;
  fail: number;
  total: number;
}) {
  const r = 48;
  const circ = 2 * Math.PI * r;
  const unk = Math.max(0, total - pass - warn - fail);

  const segs = [
    { val: pass, color: "#16a34a" },
    { val: warn, color: "#d97706" },
    { val: fail, color: "#dc2626" },
    { val: unk, color: "#cbd5e1" },
  ];

  let cursor = 0;
  const arcs = segs.map((s) => {
    const start = cursor;
    const len = total > 0 ? (s.val / total) * circ : 0;
    cursor += len;
    return { ...s, len, start };
  });

  return (
    <div className="score-ring">
      <svg viewBox="0 0 120 120" className="score-ring__svg" aria-hidden="true">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        {arcs.map((arc, i) =>
          arc.len > 0.5 ? (
            <circle
              key={i}
              cx="60"
              cy="60"
              r={r}
              fill="none"
              stroke={arc.color}
              strokeWidth="10"
              strokeLinecap="butt"
              strokeDasharray={`${arc.len} ${circ - arc.len}`}
              strokeDashoffset={-arc.start}
              style={{ transform: "rotate(-90deg)", transformOrigin: "60px 60px" }}
            />
          ) : null
        )}
      </svg>
      <div className="score-ring__center">
        <div className="score-ring__num">
          {pass}
          <span className="score-ring__den">/{total}</span>
        </div>
        <div className="score-ring__label">passing</div>
      </div>
    </div>
  );
}
