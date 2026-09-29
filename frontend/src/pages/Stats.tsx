import { useEffect, useState } from "react";

import { ApiError, getStats } from "../api/client";
import type { StatsResponse } from "../types/domain";

export function Stats() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load stats.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <section aria-labelledby="stats-heading">
      <h2 id="stats-heading">Stats</h2>

      {loading && <p data-testid="stats-loading">Loading stats…</p>}
      {error && (
        <p role="alert" data-testid="stats-error">
          {error}
        </p>
      )}

      {stats && !loading && !error && (
        <>
          {/* Showing our own cache behaviour in the UI, per the brief - the
              kind of detail that makes this feel like a real ops tool. */}
          <p data-testid="cache-status" className={`cache-badge cache-${stats.cacheStatus.toLowerCase()}`}>
            Cache: <strong>{stats.cacheStatus}</strong>
          </p>

          <p data-testid="stats-total">Total complaints: {stats.total}</p>

          <div className="stats-grid">
            <div>
              <h3>By category</h3>
              <ul>
                {Object.entries(stats.by_category).map(([category, count]) => (
                  <li key={category}>
                    {category}: {count}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3>By priority</h3>
              <ul>
                {Object.entries(stats.by_priority).map(([priority, count]) => (
                  <li key={priority}>
                    {priority}: {count}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3>By status</h3>
              <ul>
                {Object.entries(stats.by_status).map(([status, count]) => (
                  <li key={status}>
                    {status}: {count}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <button onClick={load}>Refresh</button>
        </>
      )}
    </section>
  );
}
