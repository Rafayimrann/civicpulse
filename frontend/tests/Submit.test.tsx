import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Submit } from "../src/pages/Submit";

function mockFetchOnce(status: number, body: unknown, headers: Record<string, string> = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      headers: { get: (key: string) => headers[key] ?? null },
      json: async () => body,
    }),
  );
}

describe("Submit view", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a client-side validation error and does not call the API for too-short text", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const user = userEvent.setup();

    render(<Submit />);
    await user.type(screen.getByLabelText(/what's the problem/i), "too short");
    await user.type(screen.getByLabelText(/location/i), "Street 1");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByText(/at least 10 characters/i)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("renders the loading state honestly while triage is in flight, then shows the AI result", async () => {
    let resolveFetch!: (value: unknown) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
      ),
    );
    const user = userEvent.setup();

    render(<Submit />);
    await user.type(
      screen.getByLabelText(/what's the problem/i),
      "Burst water main flooding the street near my house",
    );
    await user.type(screen.getByLabelText(/location/i), "Street 12, Block C");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    // Honest loading state: button text changes and a live-region indicator appears.
    expect(await screen.findByTestId("triaging-indicator")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /triaging with ai/i })).toBeDisabled();

    resolveFetch({
      ok: true,
      status: 201,
      headers: { get: () => null },
      json: async () => ({
        id: "abc-123",
        text: "Burst water main flooding the street near my house",
        location: "Street 12, Block C",
        reporter_contact: null,
        category: "water",
        priority: "high",
        status: "open",
        ai_summary: "Burst water main flooding street",
        triaged_by: "simulated",
        triage_latency_ms: 12,
        created_at: "2026-09-26T00:00:00Z",
        updated_at: "2026-09-26T00:00:00Z",
      }),
    });

    await waitFor(() => expect(screen.getByTestId("result-category")).toHaveTextContent("water"));
    expect(screen.getByTestId("result-priority")).toHaveTextContent("high");
    expect(screen.getByTestId("result-provider")).toHaveTextContent("simulated");
  });

  it("shows the server error message when submission fails", async () => {
    mockFetchOnce(429, { detail: "Rate limit exceeded. Please slow down." }, { "Retry-After": "30" });
    const user = userEvent.setup();

    render(<Submit />);
    await user.type(
      screen.getByLabelText(/what's the problem/i),
      "Another valid complaint body with enough characters",
    );
    await user.type(screen.getByLabelText(/location/i), "Street 5");
    await user.click(screen.getByRole("button", { name: /submit complaint/i }));

    expect(await screen.findByTestId("submit-server-error")).toHaveTextContent(/30s/);
  });
});
