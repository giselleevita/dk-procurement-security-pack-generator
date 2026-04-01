import { useState } from "react";
import { api, ApiError } from "../api/client";

type ExportFormat = "zip" | "pdf";

export function ExportButton({
  format,
  className,
  onError,
}: {
  format: ExportFormat;
  className?: string;
  onError?: (msg: string) => void;
}) {
  const [busy, setBusy] = useState(false);

  const label = format === "pdf" ? "Download branded PDF" : "Export pack (ZIP)";

  async function runExport() {
    setBusy(true);
    try {
      if (format === "pdf") {
        await api.download("/api/export/pdf", "dk-security-report.pdf");
      } else {
        await api.download("/api/export", "dk-security-pack.zip");
      }
      onError?.("");
    } catch (e) {
      onError?.(e instanceof ApiError ? JSON.stringify(e.detail) : `Failed to export ${format.toUpperCase()}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button disabled={busy} onClick={runExport} className={className}>
      {busy ? "Working..." : label}
    </button>
  );
}
