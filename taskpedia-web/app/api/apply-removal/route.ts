import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface Node {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  children_ids?: string[];
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { verbs } = body as { verbs: string[] };

    if (!verbs || !Array.isArray(verbs) || verbs.length === 0) {
      return NextResponse.json({ error: "No verbs provided" }, { status: 400 });
    }

    const verbSet = new Set(verbs.map((v) => v.toLowerCase()));

    // Load manifest
    const manifestPath = path.join(process.cwd(), "public", "data", "manifest.json");
    const data = fs.readFileSync(manifestPath, "utf-8");
    const manifest: Record<string, Node> = JSON.parse(data);

    const initialCount = Object.keys(manifest).length;

    // Find all task IDs to remove (tasks starting with any of the verbs)
    const idsToRemove = new Set<string>();

    Object.entries(manifest).forEach(([id, node]) => {
      if (node.node_type === "atomic" || node.node_type === "subtask" || node.node_type === "task") {
        const name = node.name || "";
        const firstWord = name.toLowerCase().split(/[\s,.(]/)[0].replace(/[^a-z_]/g, "");
        if (verbSet.has(firstWord)) {
          idsToRemove.add(id);
        }
      }
    });

    // Also remove all descendants of removed nodes
    const getAllDescendants = (nodeId: string): string[] => {
      const descendants: string[] = [];
      const node = manifest[nodeId];
      if (node && node.children_ids) {
        for (const childId of node.children_ids) {
          descendants.push(childId);
          descendants.push(...getAllDescendants(childId));
        }
      }
      return descendants;
    };

    const allToRemove = new Set(idsToRemove);
    for (const id of idsToRemove) {
      const descendants = getAllDescendants(id);
      descendants.forEach((d) => allToRemove.add(d));
    }

    // Remove nodes
    for (const id of allToRemove) {
      delete manifest[id];
    }

    // Update parent references - remove deleted children from children_ids
    for (const node of Object.values(manifest)) {
      if (node.children_ids) {
        node.children_ids = node.children_ids.filter((childId) => manifest[childId]);
      }
    }

    const finalCount = Object.keys(manifest).length;
    const removed = initialCount - finalCount;

    // Save updated manifest
    fs.writeFileSync(manifestPath, JSON.stringify(manifest));

    // Update stats.json
    const statsPath = path.join(process.cwd(), "public", "data", "stats.json");
    const typeCounts: Record<string, number> = {};
    for (const node of Object.values(manifest)) {
      const ntype = node.node_type || "unknown";
      typeCounts[ntype] = (typeCounts[ntype] || 0) + 1;
    }
    const stats = {
      total_nodes: finalCount,
      by_type: typeCounts,
      domains: typeCounts["domain"] || 0,
      updated_at: new Date().toISOString(),
    };
    fs.writeFileSync(statsPath, JSON.stringify(stats, null, 2));

    return NextResponse.json({
      success: true,
      removed,
      remaining: finalCount,
      verbs_processed: verbs.length,
    });
  } catch (error) {
    console.error("Error applying removal:", error);
    return NextResponse.json(
      { error: "Failed to apply removal: " + (error as Error).message },
      { status: 500 }
    );
  }
}
