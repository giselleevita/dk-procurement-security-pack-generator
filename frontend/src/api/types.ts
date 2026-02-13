export type Me = {
  id: string;
  email: string;
  created_at: string;
};

export type Connection = {
  provider: "github" | "microsoft";
  connected: boolean;
  scopes?: string;
  updated_at?: string | null;
  expires_at?: string | null;
  provider_account_id?: string | null;
};

export type ControlSummary = {
  key: string;
  provider: "github" | "microsoft" | "pack";
  title_dk: string;
  title_en: string;
  status: "pass" | "warn" | "fail" | "unknown";
  collected_at?: string | null;
};

export type ControlDetail = ControlSummary & {
  artifacts: Record<string, unknown>;
  notes: string;
};

export type CollectResponse = {
  run_id: string;
  status: "success" | "partial" | "failed";
  errors: string[];
};

