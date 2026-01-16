"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";

interface Task {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
}

interface VerbGroup {
  verb: string;
  count: number;
  tasks: Task[];
  status: "cognitive" | "physical" | "ambiguous";
}

// Known cognitive verbs - definitely non-physical
const COGNITIVE_VERBS = new Set([
  "develop", "analyze", "evaluate", "plan", "design", "create", "write",
  "prepare", "research", "study", "review", "assess", "determine",
  "recommend", "advise", "counsel", "guide", "interpret", "communicate",
  "consult", "coordinate", "manage", "supervise", "teach", "train",
  "educate", "explain", "discuss", "negotiate", "persuade", "motivate",
  "inspire", "lead", "organize", "schedule", "budget", "forecast",
  "estimate", "calculate", "compute", "compile", "document", "report",
  "present", "deliver", "conduct", "establish", "ensure", "verify",
  "confirm", "approve", "authorize", "grant", "assign", "delegate",
  "collaborate", "participate", "contribute", "support", "facilitate",
  "mediate", "resolve", "address", "identify", "recognize", "understand",
  "comprehend", "learn", "remember", "recall", "decide", "choose",
  "select", "prioritize", "consider", "think", "believe", "assume",
  "suppose", "imagine", "visualize", "conceptualize", "formulate",
  "strategize", "theorize", "hypothesize", "speculate", "predict",
  "anticipate", "expect", "hope", "wish", "want", "desire", "prefer",
  "like", "love", "hate", "fear", "worry", "doubt", "trust", "respect",
  "admire", "appreciate", "value", "judge", "criticize", "praise",
]);

// Known physical verbs - definitely robot-executable
const PHYSICAL_VERBS = new Set([
  "walk_to", "walk", "grasp", "grip", "pick_up", "pick", "place", "put",
  "push", "pull", "lift", "lower", "rotate", "turn", "press", "squeeze",
  "release", "drop", "carry", "move", "step", "reach", "extend", "bend",
  "crouch", "open", "close", "insert", "remove", "attach", "detach",
  "cut", "pour", "screw", "unscrew", "wipe", "scrub", "sweep", "fold",
  "hold", "grab", "throw", "catch", "slide", "roll", "flip", "stand",
  "sit", "lie", "kneel", "look_at", "look", "point", "touch", "tap",
  "knock", "shake", "stir", "mix", "spread", "apply", "align", "position",
  "adjust", "tighten", "loosen", "connect", "disconnect", "plug", "unplug",
  "wrap", "unwrap", "peel", "slice", "chop", "dice", "grind", "crush",
  "break", "tear", "rip", "stretch", "compress", "inflate", "deflate",
  "fill", "empty", "load", "unload", "stack", "unstack", "hang", "unhang",
  "mount", "unmount", "fasten", "unfasten", "lock", "unlock", "seal",
  "unseal", "approach", "say", "speak", "tell", "ask", "answer", "call",
]);

export default function CurateVerbsPage() {
  const [manifest, setManifest] = useState<Record<string, Task> | null>(null);
  const [loading, setLoading] = useState(true);
  const [markedForRemoval, setMarkedForRemoval] = useState<Set<string>>(new Set());
  const [markedToKeep, setMarkedToKeep] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<"all" | "cognitive" | "physical" | "ambiguous">("all");
  const [search, setSearch] = useState("");
  const [applying, setApplying] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Load manifest
  useEffect(() => {
    fetch("/data/manifest.json")
      .then((r) => r.json())
      .then((data) => {
        setManifest(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });

    // Load saved state from localStorage
    const savedRemoval = localStorage.getItem("verbs_to_remove");
    const savedKeep = localStorage.getItem("verbs_to_keep");
    if (savedRemoval) setMarkedForRemoval(new Set(JSON.parse(savedRemoval)));
    if (savedKeep) setMarkedToKeep(new Set(JSON.parse(savedKeep)));
  }, []);

  // Group tasks by verb
  const verbGroups = useMemo(() => {
    if (!manifest) return [];

    const groups: Record<string, Task[]> = {};
    Object.values(manifest).forEach((node) => {
      if (node.node_type === "atomic" || node.node_type === "subtask" || node.node_type === "task") {
        const name = node.name || "";
        const verb = name.toLowerCase().split(/[\s,.(]/)[0].replace(/[^a-z_]/g, "");
        if (verb && verb.length > 1) {
          if (!groups[verb]) groups[verb] = [];
          groups[verb].push(node);
        }
      }
    });

    return Object.entries(groups)
      .map(([verb, tasks]): VerbGroup => {
        let status: "cognitive" | "physical" | "ambiguous" = "ambiguous";
        if (COGNITIVE_VERBS.has(verb)) status = "cognitive";
        else if (PHYSICAL_VERBS.has(verb)) status = "physical";
        return { verb, count: tasks.length, tasks, status };
      })
      .sort((a, b) => b.count - a.count);
  }, [manifest]);

  // Filtered groups
  const filteredGroups = useMemo(() => {
    let groups = verbGroups;
    if (filter !== "all") {
      groups = groups.filter((g) => g.status === filter);
    }
    if (search) {
      groups = groups.filter((g) => g.verb.includes(search.toLowerCase()));
    }
    return groups;
  }, [verbGroups, filter, search]);

  // Stats
  const stats = useMemo(() => {
    const totalTasks = verbGroups.reduce((sum, g) => sum + g.count, 0);
    const toRemove = verbGroups
      .filter((g) => markedForRemoval.has(g.verb))
      .reduce((sum, g) => sum + g.count, 0);
    const toKeep = verbGroups
      .filter((g) => markedToKeep.has(g.verb))
      .reduce((sum, g) => sum + g.count, 0);
    const cognitiveTotal = verbGroups
      .filter((g) => g.status === "cognitive")
      .reduce((sum, g) => sum + g.count, 0);
    return { totalTasks, toRemove, toKeep, pending: totalTasks - toRemove - toKeep, cognitiveTotal };
  }, [verbGroups, markedForRemoval, markedToKeep]);

  const toggleRemoval = (verb: string) => {
    const newSet = new Set(markedForRemoval);
    const keepSet = new Set(markedToKeep);
    if (newSet.has(verb)) {
      newSet.delete(verb);
    } else {
      newSet.add(verb);
      keepSet.delete(verb);
    }
    setMarkedForRemoval(newSet);
    setMarkedToKeep(keepSet);
    localStorage.setItem("verbs_to_remove", JSON.stringify([...newSet]));
    localStorage.setItem("verbs_to_keep", JSON.stringify([...keepSet]));
  };

  const toggleKeep = (verb: string) => {
    const newSet = new Set(markedToKeep);
    const removeSet = new Set(markedForRemoval);
    if (newSet.has(verb)) {
      newSet.delete(verb);
    } else {
      newSet.add(verb);
      removeSet.delete(verb);
    }
    setMarkedToKeep(newSet);
    setMarkedForRemoval(removeSet);
    localStorage.setItem("verbs_to_keep", JSON.stringify([...newSet]));
    localStorage.setItem("verbs_to_remove", JSON.stringify([...removeSet]));
  };

  const markAllCognitiveForRemoval = () => {
    const newSet = new Set(markedForRemoval);
    const keepSet = new Set(markedToKeep);
    verbGroups.forEach((g) => {
      if (g.status === "cognitive") {
        newSet.add(g.verb);
        keepSet.delete(g.verb);
      }
    });
    setMarkedForRemoval(newSet);
    setMarkedToKeep(keepSet);
    localStorage.setItem("verbs_to_remove", JSON.stringify([...newSet]));
    localStorage.setItem("verbs_to_keep", JSON.stringify([...keepSet]));
  };

  const markAllPhysicalToKeep = () => {
    const newSet = new Set(markedToKeep);
    const removeSet = new Set(markedForRemoval);
    verbGroups.forEach((g) => {
      if (g.status === "physical") {
        newSet.add(g.verb);
        removeSet.delete(g.verb);
      }
    });
    setMarkedToKeep(newSet);
    setMarkedForRemoval(removeSet);
    localStorage.setItem("verbs_to_keep", JSON.stringify([...newSet]));
    localStorage.setItem("verbs_to_remove", JSON.stringify([...removeSet]));
  };

  const clearAll = () => {
    setMarkedForRemoval(new Set());
    setMarkedToKeep(new Set());
    localStorage.removeItem("verbs_to_remove");
    localStorage.removeItem("verbs_to_keep");
  };

  const exportRemovalList = () => {
    const tasksToRemove: { id: string; name: string; verb: string }[] = [];
    verbGroups.forEach((g) => {
      if (markedForRemoval.has(g.verb)) {
        g.tasks.forEach((t) => {
          tasksToRemove.push({ id: t.id, name: t.name, verb: g.verb });
        });
      }
    });
    const blob = new Blob([JSON.stringify(tasksToRemove, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tasks_to_remove_by_verb.json";
    a.click();
  };

  const applyRemoval = async () => {
    if (markedForRemoval.size === 0) {
      setMessage({ type: "error", text: "No verbs marked for removal" });
      return;
    }

    setApplying(true);
    setMessage(null);

    try {
      const verbsToRemove = [...markedForRemoval];
      const response = await fetch("/api/apply-removal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verbs: verbsToRemove }),
      });

      const result = await response.json();
      if (response.ok) {
        setMessage({ type: "success", text: `Removed ${result.removed} tasks. ${result.remaining} remaining.` });
        // Clear the marked verbs and reload manifest
        setMarkedForRemoval(new Set());
        localStorage.removeItem("verbs_to_remove");
        // Reload manifest
        const newManifest = await fetch("/data/manifest.json").then((r) => r.json());
        setManifest(newManifest);
      } else {
        setMessage({ type: "error", text: result.error || "Failed to apply removal" });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Failed to apply removal" });
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16 text-center">
        <p className="text-gray-500">Loading manifest...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <header className="mb-6">
        <Link href="/" className="text-gray-400 hover:text-gray-600 text-sm">
          ← Back to home
        </Link>
        <h1 className="text-3xl font-light mt-2 mb-1">Verb-Based Curation</h1>
        <p className="text-gray-500 text-sm">
          Remove non-physical tasks by their leading verb. Cognitive verbs are highlighted in red.
        </p>
      </header>

      {/* Stats Bar */}
      <div className="grid grid-cols-5 gap-3 mb-6">
        <div className="p-3 bg-gray-50 rounded-lg text-center">
          <p className="text-2xl font-light">{stats.totalTasks.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Total Tasks</p>
        </div>
        <div className="p-3 bg-red-50 rounded-lg text-center">
          <p className="text-2xl font-light text-red-600">{stats.toRemove.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Marked Remove</p>
        </div>
        <div className="p-3 bg-green-50 rounded-lg text-center">
          <p className="text-2xl font-light text-green-600">{stats.toKeep.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Marked Keep</p>
        </div>
        <div className="p-3 bg-yellow-50 rounded-lg text-center">
          <p className="text-2xl font-light text-yellow-600">{stats.pending.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </div>
        <div className="p-3 bg-purple-50 rounded-lg text-center">
          <p className="text-2xl font-light text-purple-600">{stats.cognitiveTotal.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Cognitive Total</p>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`mb-4 p-3 rounded-lg ${
            message.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={markAllCognitiveForRemoval}
          className="px-3 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
        >
          Mark All Cognitive for Removal ({stats.cognitiveTotal.toLocaleString()})
        </button>
        <button
          onClick={markAllPhysicalToKeep}
          className="px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
        >
          Mark All Physical to Keep
        </button>
        <button
          onClick={clearAll}
          className="px-3 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
        >
          Clear All Selections
        </button>
        <div className="flex-1" />
        <button
          onClick={exportRemovalList}
          className="px-3 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"
        >
          Export Removal List
        </button>
        <button
          onClick={applyRemoval}
          disabled={applying || markedForRemoval.size === 0}
          className={`px-4 py-2 text-sm rounded-lg ${
            applying || markedForRemoval.size === 0
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-red-600 text-white hover:bg-red-700"
          }`}
        >
          {applying ? "Applying..." : `Apply Removal (${stats.toRemove.toLocaleString()} tasks)`}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Search verbs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as typeof filter)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="all">All ({verbGroups.length})</option>
          <option value="cognitive">Cognitive ({verbGroups.filter((g) => g.status === "cognitive").length})</option>
          <option value="physical">Physical ({verbGroups.filter((g) => g.status === "physical").length})</option>
          <option value="ambiguous">Ambiguous ({verbGroups.filter((g) => g.status === "ambiguous").length})</option>
        </select>
      </div>

      {/* Verb List */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Verb</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Count</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Type</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Examples</th>
              <th className="px-4 py-2 text-right font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredGroups.map((group) => {
              const isMarkedRemove = markedForRemoval.has(group.verb);
              const isMarkedKeep = markedToKeep.has(group.verb);
              return (
                <tr
                  key={group.verb}
                  className={`border-t border-gray-100 ${
                    isMarkedRemove ? "bg-red-50" : isMarkedKeep ? "bg-green-50" : ""
                  }`}
                >
                  <td className="px-4 py-2">
                    <span className="font-mono font-medium">{group.verb}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">{group.count.toLocaleString()}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        group.status === "cognitive"
                          ? "bg-red-100 text-red-700"
                          : group.status === "physical"
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {group.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {isMarkedRemove && <span className="text-red-600 text-xs font-medium">REMOVE</span>}
                    {isMarkedKeep && <span className="text-green-600 text-xs font-medium">KEEP</span>}
                    {!isMarkedRemove && !isMarkedKeep && <span className="text-gray-400 text-xs">-</span>}
                  </td>
                  <td className="px-4 py-2 text-gray-500 text-xs max-w-md">
                    <details>
                      <summary className="cursor-pointer hover:text-gray-700">
                        Show {Math.min(5, group.tasks.length)} examples
                      </summary>
                      <ul className="mt-1 space-y-0.5 ml-2">
                        {group.tasks.slice(0, 5).map((t) => (
                          <li key={t.id} className="truncate">
                            • {t.name.slice(0, 80)}
                          </li>
                        ))}
                      </ul>
                    </details>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex gap-1 justify-end">
                      <button
                        onClick={() => toggleKeep(group.verb)}
                        className={`px-2 py-1 rounded text-xs ${
                          isMarkedKeep
                            ? "bg-green-600 text-white"
                            : "bg-green-100 text-green-700 hover:bg-green-200"
                        }`}
                      >
                        Keep
                      </button>
                      <button
                        onClick={() => toggleRemoval(group.verb)}
                        className={`px-2 py-1 rounded text-xs ${
                          isMarkedRemove
                            ? "bg-red-600 text-white"
                            : "bg-red-100 text-red-700 hover:bg-red-200"
                        }`}
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-4 text-center text-gray-400 text-xs">
        Showing {filteredGroups.length} of {verbGroups.length} verb groups
      </div>
    </div>
  );
}
