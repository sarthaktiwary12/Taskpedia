#!/usr/bin/env node

/**
 * Export TASKPEDIA data for the web app
 *
 * This script exports data from the taskpedia CLI to the visualize's public/data directory.
 * Run this before building the web app to ensure it has the latest data.
 *
 * Usage:
 *   node scripts/export-data.js
 *   npm run export-data
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const DATA_DIR = path.join(__dirname, "..", "public", "data");

console.log("📦 Exporting TASKPEDIA data for visualize...\n");

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  console.log("✓ Created data directory");
}

try {
  // Check if taskpedia CLI is available
  execSync("taskpedia --version", { stdio: "pipe" });
  console.log("✓ Found taskpedia CLI\n");

  // Export manifest as JSON
  console.log("Exporting manifest...");
  const manifestPath = path.join(DATA_DIR, "manifest.json");

  // This assumes task_hierarchy/_manifest.json exists
  const sourceManifest = path.join(
    __dirname,
    "..",
    "..",
    "task_hierarchy",
    "_manifest.json",
  );

  if (fs.existsSync(sourceManifest)) {
    fs.copyFileSync(sourceManifest, manifestPath);
    console.log("✓ Copied manifest.json");
  } else {
    console.log("⚠ Warning: No manifest found. Run taskpedia init first.");
    // Create empty manifest
    fs.writeFileSync(manifestPath, JSON.stringify({}));
  }

  // Generate statistics
  console.log("\nGenerating statistics...");
  try {
    const statsOutput = execSync("taskpedia show stats --json", {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "ignore"],
    });

    const stats = parseStatsOutput(statsOutput);
    fs.writeFileSync(
      path.join(DATA_DIR, "stats.json"),
      JSON.stringify(stats, null, 2),
    );
    console.log("✓ Generated stats.json");
  } catch (error) {
    console.log("⚠ Warning: Could not generate stats, using mock data");
    generateMockStats();
  }

  console.log("\n✅ Data export complete!");
  console.log(`   Data available in: ${DATA_DIR}`);
} catch (error) {
  console.error("❌ Error: taskpedia CLI not found");
  console.error("   Please install taskpedia first:");
  console.error("   cd .. && uv pip install -e .\n");

  console.log("📝 Generating mock data for development...");
  generateMockStats();

  console.log("\n⚠ Using mock data. Install taskpedia for real data.");
}

function parseStatsOutput(output) {
  // Parse taskpedia stats output
  // This is a placeholder - adjust based on actual output format
  try {
    return JSON.parse(output);
  } catch {
    // Fallback to mock if parsing fails
    return generateMockStats();
  }
}

function generateMockStats() {
  const mockStats = {
    totalNodes: 1000000,
    atomicActions: 750000,
    domains: 35,
    verbs: 3479,
    avgDepth: 4.2,
    maxDepth: 8,
    nodesByType: {
      DOMAIN: 35,
      TASK: 50000,
      SUBTASK: 200000,
      ATOMIC: 750000,
    },
    nodesByDomain: {
      work_healthcare: 120000,
      work_manufacturing: 95000,
      work_construction: 88000,
      work_logistics: 92000,
      work_retail: 72000,
      work_education: 68000,
      life_household: 150000,
      life_food_prep: 85000,
      life_personal_care: 75000,
      work_agriculture: 65000,
    },
    topVerbs: [
      { verb: "grasp", count: 45000 },
      { verb: "move_to", count: 42000 },
      { verb: "release", count: 38000 },
      { verb: "inspect", count: 35000 },
      { verb: "clean", count: 32000 },
      { verb: "position", count: 28000 },
      { verb: "measure", count: 25000 },
      { verb: "cut", count: 22000 },
      { verb: "assemble", count: 20000 },
      { verb: "pour", count: 18000 },
    ],
  };

  fs.writeFileSync(
    path.join(DATA_DIR, "stats.json"),
    JSON.stringify(mockStats, null, 2),
  );

  return mockStats;
}
