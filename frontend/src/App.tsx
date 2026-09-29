import { useState } from "react";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { Dashboard } from "./pages/Dashboard";
import { Stats } from "./pages/Stats";
import { Submit } from "./pages/Submit";

type View = "submit" | "dashboard" | "stats";

export function App() {
  const [view, setView] = useState<View>("submit");

  return (
    <div className="app-shell">
      <header>
        <h1>CivicPulse</h1>
        <nav aria-label="Main navigation">
          <button aria-current={view === "submit"} onClick={() => setView("submit")}>
            Submit
          </button>
          <button aria-current={view === "dashboard"} onClick={() => setView("dashboard")}>
            Dashboard
          </button>
          <button aria-current={view === "stats"} onClick={() => setView("stats")}>
            Stats
          </button>
        </nav>
      </header>

      <main>
        <ErrorBoundary>
          {view === "submit" && <Submit />}
          {view === "dashboard" && <Dashboard />}
          {view === "stats" && <Stats />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
