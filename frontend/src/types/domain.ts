// Mirrors backend/app/schemas.py. Triage category/priority and valid status
// transitions are NOT duplicated here as business rules - this file only
// describes shapes, never decides what's a valid transition. That decision
// stays server-side; the frontend just renders the server's answer
// (including its 409 message, verbatim, on an invalid attempt).

export type Category = "water" | "electricity" | "sanitation" | "roads" | "streetlights" | "other";
export type Priority = "high" | "normal" | "low";
export type ComplaintStatus = "open" | "in_progress" | "resolved" | "rejected";

export interface Complaint {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: Category;
  priority: Priority;
  status: ComplaintStatus;
  ai_summary: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
}

export interface ComplaintCreatePayload {
  text: string;
  location: string;
  reporter_contact?: string;
}

export interface StatsResponse {
  total: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  by_status: Record<string, number>;
  generated_at: string;
  cacheStatus: "HIT" | "MISS" | "UNKNOWN";
}

export interface ErrorDetail {
  field: string | null;
  message: string;
}

export interface ErrorResponse {
  detail: string;
  errors?: ErrorDetail[];
}

export interface ProvidersMeta {
  active_provider: string;
  recent_outcomes: {
    complaint_id: string;
    provider: string;
    latency_ms: number;
    fallback: boolean;
    timestamp: string;
  }[];
}
