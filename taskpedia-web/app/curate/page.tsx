"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Task {
  id: string;
  name: string;
  parent_id?: string;
}

interface CurationData {
  cognitive: Task[];
  ambiguous: Task[];
}

interface Decision {
  id: string;
  name: string;
  decision: "keep" | "remove";
  reason?: string;
}

export default function CuratePage() {
  const [data, setData] = useState<CurationData | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [mode, setMode] = useState<"bulk" | "individual">("bulk");
  const [verbFilter, setVerbFilter] = useState<string>("");
  const [stats, setStats] = useState({ kept: 0, removed: 0 });

  // Group by verb
  const getVerbGroups = (tasks: Task[]) => {
    const groups: Record<string, Task[]> = {};
    tasks.forEach((t) => {
      const verb = t.name.toLowerCase().split(/[\s_]/)[0];
      if (!groups[verb]) groups[verb] = [];
      groups[verb].push(t);
    });
    return Object.entries(groups)
      .sort((a, b) => b[1].length - a[1].length);
  };

  useEffect(() => {
    fetch("/api/curate")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);

    // Load saved decisions
    const saved = localStorage.getItem("curation_decisions");
    if (saved) {
      const parsed = JSON.parse(saved);
      setDecisions(parsed);
      setStats({
        kept: parsed.filter((d: Decision) => d.decision === "keep").length,
        removed: parsed.filter((d: Decision) => d.decision === "remove").length,
      });
    }
  }, []);

  const saveDecision = (task: Task, decision: "keep" | "remove") => {
    const newDecision: Decision = { id: task.id, name: task.name, decision };
    const updated = [...decisions.filter((d) => d.id !== task.id), newDecision];
    setDecisions(updated);
    localStorage.setItem("curation_decisions", JSON.stringify(updated));
    setStats({
      kept: updated.filter((d) => d.decision === "keep").length,
      removed: updated.filter((d) => d.decision === "remove").length,
    });
  };

  const bulkDecision = (verb: string, decision: "keep" | "remove") => {
    if (!data) return;
    const allTasks = [...data.cognitive, ...data.ambiguous];
    const matching = allTasks.filter(
      (t) => t.name.toLowerCase().split(/[\s_]/)[0] === verb
    );
    const updated = [...decisions.filter((d) =>
      !matching.some((m) => m.id === d.id)
    )];
    matching.forEach((t) => {
      updated.push({ id: t.id, name: t.name, decision });
    });
    setDecisions(updated);
    localStorage.setItem("curation_decisions", JSON.stringify(updated));
    setStats({
      kept: updated.filter((d) => d.decision === "keep").length,
      removed: updated.filter((d) => d.decision === "remove").length,
    });
  };

  const exportDecisions = () => {
    const blob = new Blob([JSON.stringify(decisions, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "curation_decisions.json";
    a.click();
  };

  if (!data) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        <p>Loading tasks to review...</p>
      </div>
    );
  }

  const allTasks = [...data.cognitive, ...data.ambiguous];
  const verbGroups = getVerbGroups(allTasks);
  const filteredGroups = verbFilter
    ? verbGroups.filter(([v]) => v.includes(verbFilter.toLowerCase()))
    : verbGroups;

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      {/* Header */}
      <header className="mb-8">
        <Link href="/" className="text-gray-400 hover:text-gray-600 text-sm">
          &larr; Back to home
        </Link>
        <h1 className="text-4xl font-light mt-4 mb-2">Task Curation</h1>
        <p className="text-gray-500">
          Review and label tasks to train the filtering algorithm
        </p>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-gray-50 rounded-lg text-center">
          <p className="text-3xl font-light">{allTasks.length}</p>
          <p className="text-sm text-gray-500">To Review</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg text-center">
          <p className="text-3xl font-light text-green-600">{stats.kept}</p>
          <p className="text-sm text-gray-500">Kept</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg text-center">
          <p className="text-3xl font-light text-red-600">{stats.removed}</p>
          <p className="text-sm text-gray-500">Removed</p>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg text-center">
          <p className="text-3xl font-light text-blue-600">
            {allTasks.length - stats.kept - stats.removed}
          </p>
          <p className="text-sm text-gray-500">Pending</p>
        </div>
      </div>

      {/* Export Button */}
      <div className="mb-8 flex gap-4">
        <button
          onClick={exportDecisions}
          className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-700"
        >
          Export Decisions (JSON)
        </button>
        <button
          onClick={() => setMode(mode === "bulk" ? "individual" : "bulk")}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          {mode === "bulk" ? "Switch to Individual" : "Switch to Bulk"}
        </button>
      </div>

      {mode === "bulk" ? (
        <>
          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Filter verbs..."
              value={verbFilter}
              onChange={(e) => setVerbFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg"
            />
          </div>

          {/* Verb Groups */}
          <div className="space-y-3">
            {filteredGroups.map(([verb, tasks]) => {
              const decidedCount = decisions.filter(
                (d) => tasks.some((t) => t.id === d.id)
              ).length;
              const keptCount = decisions.filter(
                (d) => tasks.some((t) => t.id === d.id) && d.decision === "keep"
              ).length;
              const removedCount = decidedCount - keptCount;

              return (
                <div
                  key={verb}
                  className="p-4 border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-mono text-lg">{verb}</span>
                      <span className="text-gray-400 ml-2">
                        ({tasks.length} tasks)
                      </span>
                      {decidedCount > 0 && (
                        <span className="ml-4 text-sm">
                          <span className="text-green-600">{keptCount} kept</span>
                          {" / "}
                          <span className="text-red-600">{removedCount} removed</span>
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => bulkDecision(verb, "keep")}
                        className="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Keep All
                      </button>
                      <button
                        onClick={() => bulkDecision(verb, "remove")}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Remove All
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    <details>
                      <summary className="cursor-pointer hover:text-gray-700">
                        Show examples
                      </summary>
                      <ul className="mt-2 ml-4 space-y-1">
                        {tasks.slice(0, 5).map((t) => (
                          <li key={t.id} className="truncate">
                            {t.name}
                          </li>
                        ))}
                        {tasks.length > 5 && (
                          <li className="text-gray-400">
                            ... and {tasks.length - 5} more
                          </li>
                        )}
                      </ul>
                    </details>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        /* Individual Review Mode */
        <div className="border border-gray-200 rounded-lg p-8">
          {currentIndex < allTasks.length ? (
            <>
              <p className="text-sm text-gray-400 mb-4">
                Task {currentIndex + 1} of {allTasks.length}
              </p>
              <h2 className="text-2xl mb-6">{allTasks[currentIndex].name}</h2>
              <div className="flex gap-4">
                <button
                  onClick={() => {
                    saveDecision(allTasks[currentIndex], "keep");
                    setCurrentIndex(currentIndex + 1);
                  }}
                  className="flex-1 py-3 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                >
                  Keep (Physical/Useful)
                </button>
                <button
                  onClick={() => {
                    saveDecision(allTasks[currentIndex], "remove");
                    setCurrentIndex(currentIndex + 1);
                  }}
                  className="flex-1 py-3 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                >
                  Remove (Cognitive/Vague)
                </button>
                <button
                  onClick={() => setCurrentIndex(currentIndex + 1)}
                  className="px-6 py-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  Skip
                </button>
              </div>
            </>
          ) : (
            <p className="text-center text-gray-500">
              All tasks reviewed!
            </p>
          )}
        </div>
      )}
    </div>
  );
}
