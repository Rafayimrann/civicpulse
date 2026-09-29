import { useCallback, useEffect, useState } from "react";

import { ApiError, listComplaints, updateComplaintStatus } from "../api/client";
import type { Category, Complaint, ComplaintStatus, Priority } from "../types/domain";

const PAGE_SIZE = 10;

// The frontend does NOT hardcode which transitions are valid - it just
// offers every non-current status as a candidate and lets the server be
// the single source of truth, surfacing the server's 409 message verbatim
// if the operator picks one that isn't allowed.
const ALL_STATUSES: ComplaintStatus[] = ["open", "in_progress", "resolved", "rejected"];

export function Dashboard() {
  const [items, setItems] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState<Category | "">("");
  const [priorityFilter, setPriorityFilter] = useState<Priority | "">("");
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | "">("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [transitionError, setTransitionError] = useState<{ id: string; message: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const response = await listComplaints({
        page,
        page_size: PAGE_SIZE,
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
        status: statusFilter || undefined,
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Failed to load complaints.");
    } finally {
      setLoading(false);
    }
  }, [page, categoryFilter, priorityFilter, statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleStatusChange(complaint: Complaint, newStatus: ComplaintStatus) {
    if (newStatus === complaint.status) return;
    setTransitionError(null);
    try {
      await updateComplaintStatus(complaint.id, newStatus);
      await load();
    } catch (err) {
      // Catch and display the exact server message (e.g. a 409 naming the
      // attempted transition), not a generic "error" - per the brief.
      const message = err instanceof ApiError ? err.message : "Failed to update status.";
      setTransitionError({ id: complaint.id, message });
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section aria-labelledby="dashboard-heading">
      <h2 id="dashboard-heading">Operations dashboard</h2>

      <div className="filters" role="group" aria-label="Filters">
        <label>
          Category
          <select
            value={categoryFilter}
            onChange={(e) => {
              setPage(1);
              setCategoryFilter(e.target.value as Category | "");
            }}
          >
            <option value="">All</option>
            <option value="water">Water</option>
            <option value="electricity">Electricity</option>
            <option value="sanitation">Sanitation</option>
            <option value="roads">Roads</option>
            <option value="streetlights">Streetlights</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          Priority
          <select
            value={priorityFilter}
            onChange={(e) => {
              setPage(1);
              setPriorityFilter(e.target.value as Priority | "");
            }}
          >
            <option value="">All</option>
            <option value="high">High</option>
            <option value="normal">Normal</option>
            <option value="low">Low</option>
          </select>
        </label>

        <label>
          Status
          <select
            value={statusFilter}
            onChange={(e) => {
              setPage(1);
              setStatusFilter(e.target.value as ComplaintStatus | "");
            }}
          >
            <option value="">All</option>
            {ALL_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <p data-testid="dashboard-loading">Loading complaints…</p>}
      {loadError && (
        <p role="alert" data-testid="dashboard-load-error">
          {loadError}
        </p>
      )}

      {!loading && !loadError && (
        <table data-testid="dashboard-table">
          <thead>
            <tr>
              <th>Location</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Change status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((complaint) => (
              <tr key={complaint.id} data-testid={`complaint-row-${complaint.id}`}>
                <td>{complaint.location}</td>
                <td>{complaint.category}</td>
                <td>{complaint.priority}</td>
                <td data-testid={`status-${complaint.id}`}>{complaint.status}</td>
                <td>
                  <select
                    aria-label={`Change status for complaint at ${complaint.location}`}
                    value={complaint.status}
                    onChange={(e) => handleStatusChange(complaint, e.target.value as ComplaintStatus)}
                  >
                    {ALL_STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  {transitionError?.id === complaint.id && (
                    <p role="alert" data-testid="transition-error" className="field-error">
                      {transitionError.message}
                    </p>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5}>No complaints match these filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <div className="pagination">
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span data-testid="page-indicator">
          Page {page} of {totalPages}
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
    </section>
  );
}
