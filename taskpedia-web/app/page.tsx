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
        className={`flex items-start gap-2 py-1 px-2 hover:bg-gray-50 cursor-pointer ${typeStyles[node.node_type]}`}
        onClick={() => hasChildren && setExpanded(!expanded)}
      >
        {/* Expand/collapse indicator */}
        <span className="w-4 text-gray-300 select-none flex-shrink-0">
          {hasChildren ? (expanded ? "−" : "+") : "·"}
        </span>

        {/* Node name */}
        <span className="flex-1 break-words">{node.name}</span>

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

  const domains = useMemo(() => {
    if (!manifest) return [];
    return Object.values(manifest)
      .filter(n => n.node_type === "domain")
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [manifest]);

  const stats = useMemo(() => {
    if (!manifest) return { total: 0, domains: 0, tasks: 0, subtasks: 0, atomic: 0 };
    const nodes = Object.values(manifest);
    return {
      total: nodes.length,
      domains: nodes.filter(n => n.node_type === "domain").length,
      tasks: nodes.filter(n => n.node_type === "task").length,
      subtasks: nodes.filter(n => n.node_type === "subtask").length,
      atomic: nodes.filter(n => n.node_type === "atomic").length,
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
      <header className="border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-medium">taskpedia</h1>
            <p className="text-xs text-gray-400">robot task taxonomy</p>
          </div>
          <div className="text-xs text-gray-400 text-right">
            <div>{stats.total.toLocaleString()} nodes</div>
            <div>{stats.atomic.toLocaleString()} atomic tasks</div>
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
                {searchResults.map(node => (
                  <div
                    key={node.id}
                    className="px-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        node.node_type === "atomic" ? "bg-gray-50 text-gray-400" :
                        node.node_type === "subtask" ? "bg-gray-100" :
                        node.node_type === "task" ? "bg-gray-200" : "bg-black text-white"
                      }`}>
                        {node.node_type}
                      </span>
                      <span>{node.name}</span>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1 truncate">
                      {node.id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Tree view */
            <div className="border border-gray-200 rounded">
              {domains.map(domain => (
                <div key={domain.id} className="border-b border-gray-100 last:border-0">
                  <TreeNode node={domain} manifest={manifest!} />
                </div>
              ))}
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
