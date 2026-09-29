import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "../src/pages/Dashboard";

const SAMPLE_COMPLAINT = {
  id: "11111111-1111-1111-1111-111111111111",
  text: "Burst water main flooding the street",
  location: "Street 12, Block C",
  reporter_contact: null,
  category: "water",
  priority: "high",
  status: "open",
  ai_summary: "Burst water main",
  triaged_by: "simulated",
  triage_latency_ms: 5,
  created_at: "2026-09-26T00:00:00Z",
  updated_at: "2026-09-26T00:00:00Z",
};

describe("Dashboard view", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the paginated list returned by the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: { get: () => null },
        json: async () => ({ items: [SAMPLE_COMPLAINT], total: 1, page: 1, page_size: 10 }),
      }),
    );

    render(<Dashboard />);

    expect(await screen.findByTestId(`complaint-row-${SAMPLE_COMPLAINT.id}`)).toBeInTheDocument();
    expect(screen.getByText("Street 12, Block C")).toBeInTheDocument();
    expect(screen.getByTestId("page-indicator")).toHaveTextContent("Page 1 of 1");
  });

  it("surfaces the server's exact 409 message verbatim on an invalid status transition", async () => {
    const fetchMock = vi
      .fn()
      // initial list load
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: { get: () => null },
        json: async () => ({ items: [SAMPLE_COMPLAINT], total: 1, page: 1, page_size: 10 }),
      })
      // PATCH attempt -> 409
      .mockResolvedValueOnce({
        ok: false,
        status: 409,
        headers: { get: () => null },
        json: async () => ({
          detail: "Invalid status transition: cannot move from 'open' to 'resolved'",
        }),
      });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<Dashboard />);
    await screen.findByTestId(`complaint-row-${SAMPLE_COMPLAINT.id}`);

    const select = screen.getByLabelText(/change status for complaint at street 12, block c/i);
    await user.selectOptions(select, "resolved");

    expect(await screen.findByTestId("transition-error")).toHaveTextContent(
      "Invalid status transition: cannot move from 'open' to 'resolved'",
    );
  });

  it("shows a load error message, not a blank screen, when the list request fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        headers: { get: () => null },
        json: async () => ({ detail: "Internal server error" }),
      }),
    );

    render(<Dashboard />);

    await waitFor(() => expect(screen.getByTestId("dashboard-load-error")).toBeInTheDocument());
  });
});
