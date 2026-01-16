import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface Task {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  children_ids?: string[];
  removal_reason?: string;
  review_reason?: string;
}

export async function POST(request: NextRequest) {
  try {
    const { taskId, from, to } = await request.json();

    if (!taskId || !from || !to) {
      return NextResponse.json({ error: "Missing parameters" }, { status: 400 });
    }

    const dataDir = path.join(process.cwd(), "public", "data");

    // Load all files
    const manifestPath = path.join(dataDir, "manifest.json");
    const archivePath = path.join(dataDir, "non_trainable_archive.json");
    const ambiguousPath = path.join(dataDir, "ambiguous_tasks.json");

    const manifest: Record<string, Task> = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    const archive = JSON.parse(fs.readFileSync(archivePath, "utf-8"));
    const ambiguous = JSON.parse(fs.readFileSync(ambiguousPath, "utf-8"));

    let task: Task | null = null;

    // Remove from source
    if (from === "ambiguous" && ambiguous.tasks[taskId]) {
      task = ambiguous.tasks[taskId];
      delete ambiguous.tasks[taskId];
      ambiguous.metadata.total_tasks = Object.keys(ambiguous.tasks).length;
    } else if (from === "archived" && archive.tasks[taskId]) {
      task = archive.tasks[taskId];
      delete archive.tasks[taskId];
      // Update category counts
      const verb = task.name.toLowerCase().split(/[\s,.(]/)[0];
      if (archive.metadata.categories[verb]) {
        archive.metadata.categories[verb]--;
        if (archive.metadata.categories[verb] === 0) {
          delete archive.metadata.categories[verb];
        }
      }
      archive.metadata.total_tasks = Object.keys(archive.tasks).length;
    }

    if (!task) {
      return NextResponse.json({ error: "Task not found in source" }, { status: 404 });
    }

    // Clean up task metadata
    delete task.removal_reason;
    delete task.review_reason;

    // Add to destination
    if (to === "trainable") {
      manifest[taskId] = task;
      // Try to restore parent-child relationship
      if (task.parent_id && manifest[task.parent_id]) {
        const parent = manifest[task.parent_id];
        if (!parent.children_ids) parent.children_ids = [];
        if (!parent.children_ids.includes(taskId)) {
          parent.children_ids.push(taskId);
        }
      }
    } else if (to === "archived") {
      const verb = task.name.toLowerCase().split(/[\s,.(]/)[0];
      task.removal_reason = `Manually archived: ${verb}`;
      archive.tasks[taskId] = task;
      if (!archive.metadata.categories[verb]) {
        archive.metadata.categories[verb] = 0;
      }
      archive.metadata.categories[verb]++;
      archive.metadata.total_tasks = Object.keys(archive.tasks).length;
    }

    // Save all files
    fs.writeFileSync(manifestPath, JSON.stringify(manifest));
    fs.writeFileSync(archivePath, JSON.stringify(archive, null, 2));
    fs.writeFileSync(ambiguousPath, JSON.stringify(ambiguous, null, 2));

    // Update stats
    const stats = {
      trainable: {
        total: Object.keys(manifest).length,
        by_type: {} as Record<string, number>,
      },
      non_trainable: {
        total: Object.keys(archive.tasks).length,
        by_verb: archive.metadata.categories,
      },
      ambiguous: {
        total: Object.keys(ambiguous.tasks).length,
      },
      updated_at: new Date().toISOString(),
    };

    for (const node of Object.values(manifest) as Task[]) {
      const ntype = node.node_type || "unknown";
      stats.trainable.by_type[ntype] = (stats.trainable.by_type[ntype] || 0) + 1;
    }

    fs.writeFileSync(path.join(dataDir, "stats.json"), JSON.stringify(stats, null, 2));

    return NextResponse.json({ success: true, taskId, from, to });
  } catch (error) {
    console.error("Error moving task:", error);
    return NextResponse.json({ error: (error as Error).message }, { status: 500 });
  }
}
