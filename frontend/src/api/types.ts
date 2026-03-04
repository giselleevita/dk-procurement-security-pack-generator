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
  provider: "github" | "microsoft" | "pack" | "attestation";
  title_dk: string;
  title_en: string;
  description_dk: string;
  description_en: string;
  is_attestation: boolean;
  status: "pass" | "warn" | "fail" | "unknown";
  collected_at?: string | null;
};

export type ControlDetail = ControlSummary & {
  iso27001_clauses: string[];
  nis2_articles: string[];
  remediation_dk: string;
  remediation_en: string;
  artifacts: Record<string, unknown>;
  notes: string;
};

export type CollectResponse = {
  run_id: string;
  status: "success" | "partial" | "failed";
  errors: string[];
};

export type VendorProfile = {
  company_name: string;
  cvr_number: string;
  address: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  security_officer_name: string;
  security_officer_title: string;
  pack_scope: string;
  pack_recipient: string;
  pack_validity_months: number;
  updated_at?: string | null;
};

export type AttestationStatus = "pass" | "warn" | "fail" | "unknown";

export type Attestation = {
  control_key: string;
  status: AttestationStatus;
  notes: string;
  attested_by: string;
  attested_at?: string | null;
  updated_at?: string | null;
};
