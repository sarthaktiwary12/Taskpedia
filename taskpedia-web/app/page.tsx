"use client";

import { useState, useEffect, useMemo } from "react";

interface Node {
  id: string;
  name: string;
  node_type: "domain" | "task" | "subtask" | "atomic";
  parent_id?: string;
  children_ids?: string[];
}

type Manifest = Record<string, Node>;

function TreeNode({
  node,
  manifest,
  depth = 0
}: {
  node: Node;
  manifest: Manifest;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(depth < 1);
  const children = (node.children_ids || [])
    .map(id => manifest[id])
    .filter(Boolean)
    .sort((a, b) => a.name.localeCompare(b.name));

  const hasChildren = children.length > 0;
  const isQuality = node.name.includes("(Quality)") || node.id.includes("_quality");

  const typeStyles: Record<string, string> = {
    domain: "font-medium",
    task: "text-gray-800",
    subtask: "text-gray-600",
    atomic: "text-gray-500 text-xs",
  };

  const typeBadge: Record<string, string> = {
    domain: "bg-black text-white",
    task: "bg-gray-200",
    subtask: "bg-gray-100",
    atomic: "bg-gray-50 text-gray-400",
  };

  return (
    <div className={depth > 0 ? "border-l border-gray-200 ml-2" : ""}>
      <div
        className={`flex items-start gap-2 py-1 px-2 hover:bg-gray-50 cursor-pointer ${typeStyles[node.node_type]} ${isQuality ? "bg-emerald-50/50" : ""}`}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {/* Expand/collapse indicator */}
        <span className="w-4 text-gray-300 select-none flex-shrink-0">
          {hasChildren ? (expanded ? "−" : "+") : "·"}
        </span>

        {/* Node name */}
        <span className="flex-1 break-words">{node.name}</span>

        {/* Quality badge */}
        {isQuality && (
          <span className="text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 bg-emerald-100 text-emerald-700">
            QC
          </span>
        )}

        {/* Type badge */}
        <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${typeBadge[node.node_type]}`}>
          {node.node_type}
        </span>

        {/* Child count */}
        {hasChildren && (
          <span className="text-[10px] text-gray-400 flex-shrink-0">
            {children.length}
          </span>
        )}
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div className="pl-2">
          {children.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              manifest={manifest}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/data/manifest.json")
      .then(r => r.json())
      .then(data => {
        setManifest(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // Separate robotics domains (new hierarchy) from legacy domains
  const { roboticsDomains, legacyDomains } = useMemo(() => {
    if (!manifest) return { roboticsDomains: [], legacyDomains: [] };
    const allDomains = Object.values(manifest)
      .filter(n => n.node_type === "domain")
      .sort((a, b) => a.name.localeCompare(b.name));

    return {
      roboticsDomains: allDomains.filter(d => d.id.startsWith("robotics_")),
      legacyDomains: allDomains.filter(d => !d.id.startsWith("robotics_"))
    };
  }, [manifest]);

  const [showLegacy, setShowLegacy] = useState(false);

  const stats = useMemo(() => {
    if (!manifest) return { total: 0, domains: 0, tasks: 0, subtasks: 0, atomic: 0, qualityTasks: 0, roboticsTasks: 0 };
    const nodes = Object.values(manifest);
    return {
      total: nodes.length,
      domains: nodes.filter(n => n.node_type === "domain").length,
      tasks: nodes.filter(n => n.node_type === "task").length,
      subtasks: nodes.filter(n => n.node_type === "subtask").length,
      atomic: nodes.filter(n => n.node_type === "atomic").length,
      qualityTasks: nodes.filter(n => n.id.includes("_quality")).length,
      roboticsTasks: nodes.filter(n => n.id.startsWith("robotics_")).length,
    };
  }, [manifest]);

  const searchResults = useMemo(() => {
    if (!manifest || !search || search.length < 2) return null;
    const query = search.toLowerCase();
    return Object.values(manifest)
      .filter(n => n.name.toLowerCase().includes(query))
      .slice(0, 100);
  }, [manifest, search]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center font-mono text-sm text-gray-500">
        loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-mono text-sm">
      {/* Header */}
      <header className="border-b border-gray-200 px-6 py-6 bg-gradient-to-r from-gray-50 to-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight">taskpedia</h1>
              <p className="text-sm text-gray-500">Physical Robot Task Taxonomy for Training Data</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-gray-900">{stats.total.toLocaleString()}</div>
              <div className="text-xs text-gray-500">total nodes</div>
            </div>
          </div>

          {/* Stats cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="text-lg font-semibold text-gray-900">{stats.roboticsTasks.toLocaleString()}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wide">Robotics Tasks</div>
            </div>
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
              <div className="text-lg font-semibold text-emerald-700">{stats.qualityTasks.toLocaleString()}</div>
              <div className="text-[10px] text-emerald-600 uppercase tracking-wide">Quality Controlled</div>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="text-lg font-semibold text-gray-900">{stats.subtasks.toLocaleString()}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wide">Subtasks</div>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <div className="text-lg font-semibold text-gray-900">{stats.atomic.toLocaleString()}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wide">Atomic Actions</div>
            </div>
          </div>
        </div>
      </header>

      {/* Search */}
      <div className="border-b border-gray-200 px-6 py-3">
        <div className="max-w-4xl mx-auto">
          <input
            type="text"
            placeholder="search tasks..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:border-gray-400"
          />
        </div>
      </div>

      {/* Stats bar */}
      <div className="border-b border-gray-100 px-6 py-2 bg-gray-50">
        <div className="max-w-4xl mx-auto flex gap-6 text-xs text-gray-500">
          <span>domains: {stats.domains}</span>
          <span>tasks: {stats.tasks}</span>
          <span>subtasks: {stats.subtasks}</span>
          <span>atomic: {stats.atomic}</span>
        </div>
      </div>

      {/* Main content */}
      <main className="px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {/* Search results */}
          {searchResults ? (
            <div>
              <div className="text-xs text-gray-400 mb-2">
                {searchResults.length} results {searchResults.length === 100 && "(showing first 100)"}
              </div>
              <div className="border border-gray-200 rounded">
                {searchResults.map(node => {
                  const isQuality = node.id.includes("_quality");
                  return (
                    <div
                      key={node.id}
                      className={`px-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 ${isQuality ? "bg-emerald-50/30" : ""}`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          node.node_type === "atomic" ? "bg-gray-50 text-gray-400" :
                          node.node_type === "subtask" ? "bg-gray-100" :
                          node.node_type === "task" ? "bg-gray-200" : "bg-black text-white"
                        }`}>
                          {node.node_type}
                        </span>
                        {isQuality && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                            QC
                          </span>
                        )}
                        <span>{node.name}</span>
                      </div>
                      <div className="text-[10px] text-gray-400 mt-1 truncate">
                        {node.id}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Robotics Task Categories - NEW */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-base font-semibold">Robotics Task Categories</h2>
                  <span className="text-[10px] px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full font-medium">QUALITY CONTROLLED</span>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  Physical manipulation tasks for robot training. Each task is validated to ensure it involves
                  grasping, moving, or manipulating objects - not navigation, perception, or calibration.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {roboticsDomains.map(domain => {
                    const childCount = (domain.children_ids || []).length;
                    const taskCount = (domain.children_ids || []).reduce((acc, childId) => {
                      const child = manifest![childId];
                      return acc + (child?.children_ids?.length || 0);
                    }, 0);
                    const qualityCount = (domain.children_ids || []).filter(id => id.includes("_quality")).length;
                    return (
                      <div
                        key={domain.id}
                        className="border border-gray-200 rounded-lg p-4 hover:border-emerald-400 hover:shadow-md transition-all cursor-pointer group"
                        onClick={() => {
                          const el = document.getElementById(domain.id);
                          el?.scrollIntoView({ behavior: 'smooth' });
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-semibold text-gray-900 group-hover:text-emerald-700">{domain.name}</div>
                          {qualityCount > 0 && (
                            <span className="text-[9px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded">
                              +{qualityCount} QC
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {childCount} subcategories
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {taskCount.toLocaleString()} tasks
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* QC Legend */}
                <div className="flex items-center gap-4 mb-3 text-[10px] text-gray-500">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-emerald-200 rounded"></span>
                    <span>QC = Quality Controlled (validated physical manipulation)</span>
                  </div>
                </div>

                {/* Expanded tree for robotics domains */}
                <div className="border border-gray-200 rounded">
                  {roboticsDomains.map(domain => (
                    <div key={domain.id} id={domain.id} className="border-b border-gray-100 last:border-0">
                      <TreeNode node={domain} manifest={manifest!} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Legacy domains toggle */}
              <div>
                <button
                  onClick={() => setShowLegacy(!showLegacy)}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  <span>{showLegacy ? "−" : "+"}</span>
                  <span>Legacy Data ({legacyDomains.length} domains)</span>
                </button>

                {showLegacy && (
                  <div className="border border-gray-200 rounded mt-3">
                    {legacyDomains.map(domain => (
                      <div key={domain.id} className="border-b border-gray-100 last:border-0">
                        <TreeNode node={domain} manifest={manifest!} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-6 py-4 mt-8">
        <div className="max-w-4xl mx-auto text-xs text-gray-400 flex gap-6">
          <a href="/data-overview" className="hover:text-gray-600 underline">data overview</a>
          <a href="/curate-verbs" className="hover:text-gray-600 underline">curate</a>
        </div>
      </footer>
    </div>
  );
}
