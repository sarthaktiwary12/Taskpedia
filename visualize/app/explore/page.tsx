import { Suspense } from "react";
import type { Metadata } from "next";
import { Search } from "lucide-react";
import { ExploreClient } from "@/components/ExploreClient";
import fs from "fs";
import path from "path";

export const dynamic = "force-static";
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Explore",
  description:
    "Search and explore millions of atomic robot-executable actions across 35+ domains.",
};

async function getInitialData() {
  try {
    const manifestPath = path.join(
      process.cwd(),
      "public",
      "data",
      "manifest.json",
    );
    const data = fs.readFileSync(manifestPath, "utf-8");
    const manifest = JSON.parse(data);

    // Get domains (top-level nodes)
    const domains = Object.values(manifest)
      .filter((node: any) => node.node_type?.toUpperCase() === "DOMAIN")
      .slice(0, 20);

    // Get sample atomic actions
    const atomicSamples = Object.values(manifest)
      .filter((node: any) => node.node_type?.toUpperCase() === "ATOMIC")
      .slice(0, 50);

    return { domains, atomicSamples, totalNodes: Object.keys(manifest).length };
  } catch {
    return { domains: [], atomicSamples: [], totalNodes: 0 };
  }
}

export default async function ExplorePage() {
  const { domains, atomicSamples, totalNodes } = await getInitialData();

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">Explore Dataset</span>
          </h1>
          <p className="text-lg text-white/50">
            Search through {totalNodes.toLocaleString()} hierarchical task nodes
          </p>
        </div>

        <Suspense fallback={<SearchSkeleton />}>
          <ExploreClient domains={domains} samples={atomicSamples} />
        </Suspense>
      </div>
    </div>
  );
}

function SearchSkeleton() {
  return (
    <div className="space-y-6">
      <div className="glass rounded-2xl p-6">
        <div className="h-14 skeleton rounded-xl" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-32 skeleton rounded-xl" />
        ))}
      </div>
    </div>
  );
}
