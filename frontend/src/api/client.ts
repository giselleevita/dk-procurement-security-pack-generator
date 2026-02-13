const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getCookie(name: string): string | null {
  const parts = document.cookie.split(";").map((p) => p.trim());
  for (const p of parts) {
    if (p.startsWith(name + "=")) return decodeURIComponent(p.slice(name.length + 1));
  }
  return null;
}

function csrfToken(): string | null {
  return getCookie("dkpack_csrf");
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

type Method = "GET" | "POST" | "DELETE";

async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";

  if (method !== "GET") {
    const csrf = csrfToken();
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    method,
    credentials: "include",
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    let detail: unknown = null;
    try {
      detail = await resp.json();
    } catch {
      detail = await resp.text();
    }
    throw new ApiError(resp.status, detail);
  }

  // 204 or empty body
  const text = await resp.text();
  return (text ? (JSON.parse(text) as T) : ({} as T));
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
  download: async (path: string, filename: string) => {
    const headers: Record<string, string> = {};
    const csrf = csrfToken();
    if (csrf) headers["X-CSRF-Token"] = csrf;

    const resp = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers,
    });
    if (!resp.ok) throw new ApiError(resp.status, await resp.text());

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

