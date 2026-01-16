"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Task {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  removal_reason?: string;
  review_reason?: string;
}

interface Stats {
  trainable: { total: number; by_type: Record<string, number> };
  non_trainable: { total: number; by_verb: Record<string, number> };
  ambiguous: { total: number };
}

export default function DataOverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeTab, setActiveTab] = useState<"trainable" | "archived" | "ambiguous">("trainable");
  const [trainable, setTrainable] = useState<Record<string, Task>>({});
  const [archived, setArchived] = useState<{ tasks: Record<string, Task>; metadata: any }>({ tasks: {}, metadata: {} });
  const [ambiguous, setAmbiguous] = useState<{ tasks: Record<string, Task>; metadata: any }>({ tasks: {}, metadata: {} });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/data/stats.json").then(r => r.json()),
      fetch("/data/manifest.json").then(r => r.json()),
      fetch("/data/non_trainable_archive.json").then(r => r.json()).catch(() => ({ tasks: {}, metadata: {} })),
      fetch("/data/ambiguous_tasks.json").then(r => r.json()).catch(() => ({ tasks: {}, metadata: {} })),
    ]).then(([statsData, trainableData, archivedData, ambiguousData]) => {
      setStats(statsData);
      setTrainable(trainableData);
      setArchived(archivedData);
      setAmbiguous(ambiguousData);
      setLoading(false);
    });
  }, []);

  const moveTask = async (taskId: string, from: "ambiguous" | "archived", to: "trainable" | "archived") => {
    setProcessing(true);
    try {
      const response = await fetch("/api/move-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ taskId, from, to }),
      });
      if (response.ok) {
        // Reload data
        const [newTrainable, newArchived, newAmbiguous, newStats] = await Promise.all([
          fetch("/data/manifest.json").then(r => r.json()),
          fetch("/data/non_trainable_archive.json").then(r => r.json()),
          fetch("/data/ambiguous_tasks.json").then(r => r.json()),
          fetch("/data/stats.json").then(r => r.json()),
        ]);
        setTrainable(newTrainable);
        setArchived(newArchived);
        setAmbiguous(newAmbiguous);
        setStats(newStats);
        setMessage(`Moved task to ${to}`);
        setTimeout(() => setMessage(null), 2000);
      }
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const getFilteredTasks = () => {
    let tasks: [string, Task][] = [];
    if (activeTab === "trainable") {
      tasks = Object.entries(trainable).filter(([_, t]) => t.node_type !== "domain");
    } else if (activeTab === "archived") {
      tasks = Object.entries(archived.tasks || {});
    } else {
      tasks = Object.entries(ambiguous.tasks || {});
    }

    if (search) {
      tasks = tasks.filter(([_, t]) => t.name.toLowerCase().includes(search.toLowerCase()));
    }
    return tasks.slice(0, 200); // Limit display
  };

  if (loading) {
    return <div className="max-w-6xl mx-auto px-6 py-16 text-center">Loading...</div>;
  }

  const filteredTasks = getFilteredTasks();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <header className="mb-6">
        <Link href="/" className="text-gray-400 hover:text-gray-600 text-sm">← Back to home</Link>
        <h1 className="text-3xl font-light mt-2">Data Overview</h1>
        <p className="text-gray-500 text-sm">Manage trainable vs non-trainable task separation</p>
      </header>

      {message && (
        <div className="mb-4 p-3 bg-green-100 text-green-800 rounded-lg">{message}</div>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => setActiveTab("trainable")}
          className={`p-4 rounded-lg text-left transition ${
            activeTab === "trainable" ? "bg-green-100 border-2 border-green-500" : "bg-gray-50 hover:bg-gray-100"
          }`}
        >
          <p className="text-3xl font-light text-green-600">{stats?.trainable.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 font-medium">Trainable Tasks</p>
          <p className="text-xs text-gray-400 mt-1">Physical, robot-executable</p>
        </button>
        <button
          onClick={() => setActiveTab("archived")}
          className={`p-4 rounded-lg text-left transition ${
            activeTab === "archived" ? "bg-red-100 border-2 border-red-500" : "bg-gray-50 hover:bg-gray-100"
          }`}
        >
          <p className="text-3xl font-light text-red-600">{stats?.non_trainable.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 font-medium">Non-Trainable (Archived)</p>
          <p className="text-xs text-gray-400 mt-1">Cognitive, abstract tasks</p>
        </button>
        <button
          onClick={() => setActiveTab("ambiguous")}
          className={`p-4 rounded-lg text-left transition ${
            activeTab === "ambiguous" ? "bg-yellow-100 border-2 border-yellow-500" : "bg-gray-50 hover:bg-gray-100"
          }`}
        >
          <p className="text-3xl font-light text-yellow-600">{stats?.ambiguous.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 font-medium">Needs Review</p>
          <p className="text-xs text-gray-400 mt-1">Ambiguous - decide trainable or not</p>
        </button>
      </div>

      {/* Breakdown */}
      {activeTab === "trainable" && stats && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-medium text-green-800 mb-2">Trainable Tasks by Type</h3>
          <div className="flex gap-4 text-sm">
            {Object.entries(stats.trainable.by_type).map(([type, count]) => (
              <span key={type} className="text-green-700">
                {type}: <strong>{count.toLocaleString()}</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {activeTab === "archived" && stats && (
        <div className="mb-6 p-4 bg-red-50 rounded-lg">
          <h3 className="font-medium text-red-800 mb-2">Archived by Verb (Non-Physical)</h3>
          <div className="flex flex-wrap gap-2 text-sm">
            {Object.entries(stats.non_trainable.by_verb || {})
              .sort((a, b) => b[1] - a[1])
              .map(([verb, count]) => (
                <span key={verb} className="px-2 py-1 bg-red-100 rounded text-red-700">
                  {verb}: {count}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2 border border-gray-200 rounded-lg"
        />
      </div>

      {/* Task List */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Task Name</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
              {(activeTab === "archived" || activeTab === "ambiguous") && (
                <th className="px-4 py-2 text-left font-medium text-gray-600">Reason</th>
              )}
              {activeTab !== "trainable" && (
                <th className="px-4 py-2 text-right font-medium text-gray-600">Actions</th>
              )}
            </tr>
          </thead>
          <tbody>
            {filteredTasks.map(([id, task]) => (
              <tr key={id} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-2">
                  <span className="block truncate max-w-lg" title={task.name}>
                    {task.name}
                  </span>
                  <span className="text-xs text-gray-400 truncate block">{id}</span>
                </td>
                <td className="px-4 py-2 text-gray-500">{task.node_type}</td>
                {(activeTab === "archived" || activeTab === "ambiguous") && (
                  <td className="px-4 py-2 text-xs text-gray-500">
                    {task.removal_reason || task.review_reason || "-"}
                  </td>
                )}
                {activeTab === "ambiguous" && (
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => moveTask(id, "ambiguous", "trainable")}
                      disabled={processing}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 mr-1"
                    >
                      → Trainable
                    </button>
                    <button
                      onClick={() => moveTask(id, "ambiguous", "archived")}
                      disabled={processing}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                      → Archive
                    </button>
                  </td>
                )}
                {activeTab === "archived" && (
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => moveTask(id, "archived", "trainable")}
                      disabled={processing}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      Restore → Trainable
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {filteredTasks.length === 200 && (
          <div className="p-2 bg-gray-50 text-center text-xs text-gray-500">
            Showing first 200 results. Use search to filter.
          </div>
        )}
      </div>
    </div>
  );
}
