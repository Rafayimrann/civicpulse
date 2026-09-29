import type {
  Complaint,
  ComplaintCreatePayload,
  ComplaintListResponse,
  ComplaintStatus,
  ErrorResponse,
  ProvidersMeta,
  StatsResponse,
} from "../types/domain";

// Every call below hits a path starting with "/api" and nothing else - no
// import.meta.env.VITE_API_URL, no absolute host. In dev, Vite's proxy
// (vite.config.ts) forwards these to the backend container; in production,
// nginx does the same. That is what makes one built image environment-
// agnostic (see the docs/adr/0002-frontend-runtime-config.md note).

export class ApiError extends Error {
  status: number;
  detail: string;
  fieldErrors: { field: string | null; message: string }[];

  constructor(status: number, body: ErrorResponse | { detail?: string }) {
    const detail = ("detail" in body && body.detail) || "Request failed";
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.fieldErrors = "errors" in body && body.errors ? body.errors : [];
  }
}

async function parseErrorBody(response: Response): Promise<ErrorResponse> {
  try {
    return (await response.json()) as ErrorResponse;
  } catch {
    return { detail: `Request failed with status ${response.status}` };
  }
}

export async function createComplaint(payload: ComplaintCreatePayload): Promise<Complaint> {
  const response = await fetch("/api/complaints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (response.status === 429) {
    const retryAfter = response.headers.get("Retry-After");
    const body = await parseErrorBody(response);
    const err = new ApiError(429, body);
    err.message = retryAfter
      ? `Rate limit exceeded. Try again in ${retryAfter}s.`
      : body.detail;
    throw err;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  return (await response.json()) as Complaint;
}

export interface ListComplaintsParams {
  page?: number;
  page_size?: number;
  category?: string;
  priority?: string;
  status?: string;
}

export async function listComplaints(params: ListComplaintsParams = {}): Promise<ComplaintListResponse> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  if (params.category) search.set("category", params.category);
  if (params.priority) search.set("priority", params.priority);
  if (params.status) search.set("status", params.status);

  const response = await fetch(`/api/complaints?${search.toString()}`);
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  return (await response.json()) as ComplaintListResponse;
}

export async function getComplaint(id: string): Promise<Complaint> {
  const response = await fetch(`/api/complaints/${id}`);
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  return (await response.json()) as Complaint;
}

export async function updateComplaintStatus(id: string, status: ComplaintStatus): Promise<Complaint> {
  const response = await fetch(`/api/complaints/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    // Surfaces the server's exact 409 message (e.g. "Invalid status
    // transition: cannot move from 'open' to 'resolved'") to the caller
    // verbatim, per the brief - never a generic "error".
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  return (await response.json()) as Complaint;
}

export async function getStats(): Promise<StatsResponse> {
  const response = await fetch("/api/stats");
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  const data = await response.json();
  const cacheStatus = (response.headers.get("X-Cache") as "HIT" | "MISS" | null) ?? "UNKNOWN";
  return { ...data, cacheStatus };
}

export async function getProvidersMeta(): Promise<ProvidersMeta> {
  const response = await fetch("/api/meta/providers");
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }
  return (await response.json()) as ProvidersMeta;
}
