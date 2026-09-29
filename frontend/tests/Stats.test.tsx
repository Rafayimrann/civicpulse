import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Stats } from "../src/pages/Stats";

const STATS_BODY = {
  total: 3,
  by_category: { water: 2, roads: 1 },
  by_priority: { high: 1, normal: 2 },
  by_status: { open: 3 },
  generated_at: "2026-09-26T00:00:00Z",
};

describe("Stats view", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders aggregate counts and explicitly shows a cache MISS from the X-Cache header", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: { get: (key: string) => (key === "X-Cache" ? "MISS" : null) },
        json: async () => STATS_BODY,
      }),
    );

    render(<Stats />);

    expect(await screen.findByTestId("cache-status")).toHaveTextContent("MISS");
    expect(screen.getByTestId("stats-total")).toHaveTextContent("3");
  });

  it("renders a cache HIT badge distinctly when the X-Cache header says HIT", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: { get: (key: string) => (key === "X-Cache" ? "HIT" : null) },
        json: async () => STATS_BODY,
      }),
    );

    render(<Stats />);

    const badge = await screen.findByTestId("cache-status");
    expect(badge).toHaveTextContent("HIT");
    expect(badge.className).toContain("cache-hit");
  });
});
