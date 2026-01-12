#!/usr/bin/env node

/**
 * Export TASKPEDIA data for the web app
 * Reads real data from task_hierarchy/_manifest.json
 */

const fs = require("fs");
const path = require("path");

const DATA_DIR = path.join(__dirname, "..", "public", "data");
const TASK_HIERARCHY_DIR = path.join(__dirname, "..", "..", "task_hierarchy");
const MANIFEST_PATH = path.join(TASK_HIERARCHY_DIR, "_manifest.json");

console.log("Exporting TASKPEDIA data for webapp...\n");

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Check if real manifest exists
if (!fs.existsSync(MANIFEST_PATH)) {
  console.error("Error: task_hierarchy/_manifest.json not found!");
  console.error("Run 'taskpedia init' first to generate the hierarchy.");
  process.exit(1);
}

console.log("Loading manifest from:", MANIFEST_PATH);
const rawManifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf-8"));

// Handle nested structure: { version, node_count, nodes: {...} }
const manifestData = rawManifest.nodes || rawManifest;
const nodes = Object.values(manifestData);

console.log(`Found ${nodes.length} nodes\n`);

// Compute real statistics
const stats = {
  totalNodes: nodes.length,
  atomicActions: 0,
  domains: 0,
  verbs: 0,
  avgDepth: 0,
  maxDepth: 0,
  nodesByType: {
    DOMAIN: 0,
    TASK: 0,
    SUBTASK: 0,
    ATOMIC: 0,
  },
  nodesByDomain: {},
  topVerbs: [],
};

const verbCounts = {};
let totalDepth = 0;

for (const node of nodes) {
  // Count by type (handle both uppercase and lowercase)
  const nodeType = (node.node_type || "UNKNOWN").toUpperCase();
  if (stats.nodesByType[nodeType] !== undefined) {
    stats.nodesByType[nodeType]++;
  }

  if (nodeType === "ATOMIC") {
    stats.atomicActions++;
  }

  if (nodeType === "DOMAIN") {
    stats.domains++;
  }

  // Count by domain (first part of id)
  const domain = node.id ? node.id.split("/")[0] : "unknown";
  stats.nodesByDomain[domain] = (stats.nodesByDomain[domain] || 0) + 1;

  // Extract verb from name (first word)
  if (nodeType === "ATOMIC" && node.name) {
    const verb = node.name.split(/[\s_]/)[0].toLowerCase();
    if (verb && verb.length > 1) {
      verbCounts[verb] = (verbCounts[verb] || 0) + 1;
    }
  }

  // Calculate depth from id path
  if (node.id) {
    const depth = node.id.split("/").length;
    totalDepth += depth;
    if (depth > stats.maxDepth) {
      stats.maxDepth = depth;
    }
  }
}

// Calculate average depth
stats.avgDepth = nodes.length > 0 ? (totalDepth / nodes.length).toFixed(2) : 0;
stats.avgDepth = parseFloat(stats.avgDepth);

// Get unique verbs count and top verbs
const sortedVerbs = Object.entries(verbCounts).sort(([, a], [, b]) => b - a);

stats.verbs = sortedVerbs.length;
stats.topVerbs = sortedVerbs
  .slice(0, 20)
  .map(([verb, count]) => ({ verb, count }));

// Sort domains by count (top 15)
const sortedDomains = Object.entries(stats.nodesByDomain)
  .sort(([, a], [, b]) => b - a)
  .slice(0, 15);
stats.nodesByDomain = Object.fromEntries(sortedDomains);

// Write stats
fs.writeFileSync(
  path.join(DATA_DIR, "stats.json"),
  JSON.stringify(stats, null, 2),
);
console.log("Generated stats.json");

// Copy manifest (or create a smaller version for web)
// For large datasets, we might want to create an index instead
const manifestSize = Buffer.byteLength(JSON.stringify(manifestData));
console.log(`Manifest size: ${(manifestSize / 1024 / 1024).toFixed(2)} MB`);

if (manifestSize > 10 * 1024 * 1024) {
  // If > 10MB, create a lighter version with just essential fields
  console.log("Creating optimized manifest for web...");
  const lightManifest = {};
  for (const [id, node] of Object.entries(manifestData)) {
    lightManifest[id] = {
      id: node.id,
      name: node.name,
      node_type: node.node_type,
      parent_id: node.parent_id,
      children_ids: node.children_ids || [],
    };
  }
  fs.writeFileSync(
    path.join(DATA_DIR, "manifest.json"),
    JSON.stringify(lightManifest),
  );
} else {
  fs.copyFileSync(MANIFEST_PATH, path.join(DATA_DIR, "manifest.json"));
}
console.log("Generated manifest.json");

console.log("\n✅ Data export complete!");
console.log(`   Data available in: ${DATA_DIR}`);
console.log(`\nStatistics:`);
console.log(`   Total nodes: ${stats.totalNodes.toLocaleString()}`);
console.log(`   Atomic actions: ${stats.atomicActions.toLocaleString()}`);
console.log(`   Domains: ${stats.domains}`);
console.log(`   Unique verbs: ${stats.verbs}`);
console.log(`   Max depth: ${stats.maxDepth}`);
console.log(`   Avg depth: ${stats.avgDepth}`);
