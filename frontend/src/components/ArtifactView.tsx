import { relTime } from "../utils/time";

function humanKey(k: string): string {
  return k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Val({ v }: { v: unknown }): React.ReactElement {
  if (v === true) return <span className="av-true">✓ Yes</span>;
  if (v === false) return <span className="av-false">✗ No</span>;
  if (v === null || v === undefined) return <span className="av-null">—</span>;
  if (typeof v === "number") return <strong>{v.toLocaleString()}</strong>;
  if (typeof v === "string") {
    if (/^\d{4}-\d{2}-\d{2}T/.test(v)) return <span title={v}>{relTime(v)}</span>;
    if (v.length > 160) return <span className="av-long">{v.slice(0, 160)}…</span>;
    return <span>{v}</span>;
  }
  if (Array.isArray(v)) {
    if (v.length === 0) return <span className="av-null">Empty</span>;
    if (typeof v[0] === "object" && v[0] !== null) {
      const keys = Object.keys(v[0] as object).slice(0, 7);
      return (
        <div className="av-table-wrap">
          <table className="av-table">
            <thead>
              <tr>
                {keys.map((k) => (
                  <th key={k}>{humanKey(k)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(v as Record<string, unknown>[]).slice(0, 15).map((row, i) => (
                <tr key={i}>
                  {keys.map((k) => (
                    <td key={k}>
                      <Val v={row[k]} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {v.length > 15 && <p className="av-more muted">… and {v.length - 15} more rows</p>}
        </div>
      );
    }
    return (
      <ul className="av-list">
        {v.slice(0, 20).map((item, i) => (
          <li key={i}>
            <Val v={item} />
          </li>
        ))}
        {v.length > 20 && <li className="av-null">… {v.length - 20} more</li>}
      </ul>
    );
  }
  if (typeof v === "object") {
    return <ObjView obj={v as Record<string, unknown>} />;
  }
  return <span>{String(v)}</span>;
}

function ObjView({ obj }: { obj: Record<string, unknown> }) {
  const entries = Object.entries(obj);
  if (entries.length === 0) return <span className="av-null">Empty</span>;
  return (
    <dl className="av-kv">
      {entries.map(([k, v]) => (
        <div key={k} className="av-kv__row">
          <dt>{humanKey(k)}</dt>
          <dd>
            <Val v={v} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function ArtifactView({ artifacts }: { artifacts: Record<string, unknown> }) {
  if (!artifacts || Object.keys(artifacts).length === 0) {
    return <p className="muted av-empty">No artifact data collected yet.</p>;
  }
  return <ObjView obj={artifacts} />;
}
