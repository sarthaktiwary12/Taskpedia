import { notFound } from "next/navigation";
import Link from "next/link";
import fs from "fs";
import path from "path";

export const dynamic = "force-static";

interface Node {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  children_ids?: string[];
  description?: string;
}

async function getManifest(): Promise<Record<string, Node>> {
  try {
    const manifestPath = path.join(process.cwd(), "public", "data", "manifest.json");
    const data = fs.readFileSync(manifestPath, "utf-8");
    return JSON.parse(data);
  } catch {
    return {};
  }
}

export async function generateStaticParams() {
  const manifest = await getManifest();
  return Object.keys(manifest).map((id) => ({
    id: encodeURIComponent(id),
  }));
}

interface Props {
  params: Promise<{ id: string }>;
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

  const typeLabel: Record<string, string> = {
    domain: "Category",
    task: "Task",
    subtask: "Subtask",
    atomic: "Atomic Action",
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      {/* Breadcrumb */}
      <nav className="mb-12">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Link href="/" className="hover:text-gray-600">
            Home
          </Link>
          {breadcrumbs.map((b) => (
            <span key={b.id} className="flex items-center gap-2">
              <span>/</span>
              <Link
                href={`/node/${encodeURIComponent(b.id)}`}
                className={`hover:text-gray-600 ${
                  b.id === node.id ? "text-gray-900" : ""
                }`}
              >
                {b.name}
              </Link>
            </span>
          ))}
        </div>
      </nav>

      {/* Node Info */}
      <header className="mb-12">
        <p className="text-sm uppercase tracking-widest text-gray-400 mb-2">
          {typeLabel[node.node_type] || node.node_type}
        </p>
        <h1 className="text-4xl font-light tracking-tight mb-4">
          {node.name}
        </h1>
        {node.description && (
          <p className="text-gray-500">{node.description}</p>
        )}
      </header>

      {/* Children */}
      {children.length > 0 && (
        <section>
          <h2 className="text-sm uppercase tracking-widest text-gray-400 mb-6">
            {node.node_type === "domain" ? "Tasks" : "Subtasks"} ({children.length})
          </h2>

          <div className="space-y-3">
            {children.map((child) => (
              <Link
                key={child.id}
                href={`/node/${encodeURIComponent(child.id)}`}
                className="block py-4 px-6 border border-gray-200 rounded-lg hover:border-gray-400 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-lg">{child.name}</span>
                  {child.children_ids && child.children_ids.length > 0 && (
                    <span className="text-sm text-gray-400">
                      {child.children_ids.length} subtasks
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Atomic action indicator */}
      {children.length === 0 && (
        <div className="py-8 px-6 bg-gray-50 rounded-lg text-center">
          <p className="text-gray-500">
            {node.node_type === "atomic"
              ? "This is an atomic action - a single robot-executable primitive"
              : "No subtasks yet"}
          </p>
        </div>
      )}

      {/* Back link */}
      <div className="mt-12 pt-8 border-t border-gray-200">
        {node.parent_id ? (
          <Link
            href={`/node/${encodeURIComponent(node.parent_id)}`}
            className="text-gray-400 hover:text-gray-600"
          >
            &larr; Back to {manifest[node.parent_id]?.name || "parent"}
          </Link>
        ) : (
          <Link href="/" className="text-gray-400 hover:text-gray-600">
            &larr; Back to all categories
          </Link>
        )}
      </div>
    </div>
  );
}
