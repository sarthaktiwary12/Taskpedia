import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronRight, ArrowLeft, Zap, GitBranch } from "lucide-react";
import fs from "fs";
import path from "path";

export const dynamic = "force-static";
export const revalidate = 3600;

interface Node {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  children_ids?: string[];
}

async function getManifest(): Promise<Record<string, Node>> {
  try {
    const manifestPath = path.join(
      process.cwd(),
      "public",
      "data",
      "manifest.json",
    );
    const data = fs.readFileSync(manifestPath, "utf-8");
    return JSON.parse(data);
  } catch {
    return {};
  }
}

export async function generateStaticParams() {
  const manifest = await getManifest();
  // Generate params for top-level nodes only to avoid huge build
  const topNodes = Object.values(manifest)
    .filter(
      (node) => !node.parent_id || node.node_type?.toUpperCase() === "DOMAIN",
    )
    .slice(0, 100);

  return topNodes.map((node) => ({
    id: encodeURIComponent(node.id),
  }));
}

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const manifest = await getManifest();
  const node = manifest[decodeURIComponent(id)];

  if (!node) {
    return { title: "Node Not Found" };
  }

  return {
    title: node.name,
    description: `Explore "${node.name}" - a ${node.node_type} in TASKPEDIA.`,
  };
}

export default async function NodePage({ params }: Props) {
  const { id } = await params;
  const nodeId = decodeURIComponent(id);
  const manifest = await getManifest();
  const node = manifest[nodeId];

  if (!node) {
    notFound();
  }

  // Get children
  const children = (node.children_ids || [])
    .map((childId) => manifest[childId])
    .filter(Boolean);

  // Build breadcrumb path
  const breadcrumbs: Node[] = [];
  let current: Node | undefined = node;
  while (current) {
    breadcrumbs.unshift(current);
    current = current.parent_id ? manifest[current.parent_id] : undefined;
  }

  const typeColors: Record<string, string> = {
    DOMAIN: "from-blue-500 to-cyan-500",
    TASK: "from-violet-500 to-purple-500",
    SUBTASK: "from-orange-500 to-amber-500",
    ATOMIC: "from-emerald-500 to-green-500",
  };

  const nodeType = node.node_type?.toUpperCase() || "UNKNOWN";
  const gradient = typeColors[nodeType] || "from-gray-500 to-gray-600";

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back */}
        <Link
          href="/explore"
          className="inline-flex items-center gap-2 text-white/50 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Explore
        </Link>

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm mb-8 overflow-x-auto pb-2">
          {breadcrumbs.map((b, idx) => (
            <span
              key={b.id}
              className="flex items-center gap-2 whitespace-nowrap"
            >
              {idx > 0 && <ChevronRight className="w-4 h-4 text-white/30" />}
              <Link
                href={`/node/${encodeURIComponent(b.id)}`}
                className={`hover:text-violet-400 transition-colors ${
                  idx === breadcrumbs.length - 1
                    ? "text-white font-medium"
                    : "text-white/50"
                }`}
              >
                {b.name}
              </Link>
            </span>
          ))}
        </nav>

        {/* Node Card */}
        <div className="glass rounded-2xl p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold bg-gradient-to-r ${gradient} text-white`}
            >
              {nodeType}
            </span>
            {nodeType === "ATOMIC" && (
              <Zap className="w-5 h-5 text-emerald-400" />
            )}
          </div>

          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {node.name}
          </h1>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-white/5 rounded-xl">
            <div>
              <p className="text-xs text-white/40 uppercase mb-1">ID</p>
              <p className="text-sm font-mono text-white/80 break-all">
                {node.id}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/40 uppercase mb-1">Type</p>
              <p className="text-sm text-white/80">{nodeType}</p>
            </div>
            <div>
              <p className="text-xs text-white/40 uppercase mb-1">Children</p>
              <p className="text-sm text-white/80">{children.length}</p>
            </div>
          </div>
        </div>

        {/* Children */}
        {children.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-violet-400" />
              Child Nodes ({children.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {children.map((child) => {
                const childType = child.node_type?.toUpperCase() || "UNKNOWN";
                const childGradient =
                  typeColors[childType] || "from-gray-500 to-gray-600";

                return (
                  <Link
                    key={child.id}
                    href={`/node/${encodeURIComponent(child.id)}`}
                    className="glass rounded-xl p-5 hover:bg-white/10 transition-all group"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <span
                        className={`px-2 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r ${childGradient} text-white`}
                      >
                        {childType}
                      </span>
                      <ChevronRight className="w-5 h-5 text-white/30 group-hover:text-white/60 group-hover:translate-x-1 transition-all" />
                    </div>
                    <h3 className="text-lg font-semibold text-white group-hover:text-violet-300 transition-colors">
                      {child.name}
                    </h3>
                    {child.children_ids && child.children_ids.length > 0 && (
                      <p className="text-xs text-white/30 mt-2">
                        {child.children_ids.length} children
                      </p>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {children.length === 0 && nodeType === "ATOMIC" && (
          <div className="glass rounded-2xl p-8 text-center">
            <Zap className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
            <p className="text-white/60">
              This is an atomic action - a robot-executable primitive
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
