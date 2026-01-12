import type { Metadata } from "next";
import {
  Database,
  Zap,
  GitBranch,
  Cpu,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import fs from "fs";
import path from "path";

export const dynamic = "force-static";
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Statistics",
  description:
    "Comprehensive statistics and analytics for the TASKPEDIA dataset.",
};

async function getStats() {
  try {
    const statsPath = path.join(process.cwd(), "public", "data", "stats.json");
    const data = fs.readFileSync(statsPath, "utf-8");
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export default async function StatsPage() {
  const stats = await getStats();

  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-white/50">
          Stats not available. Run export-data first.
        </p>
      </div>
    );
  }

  const nodeTypeData = Object.entries(stats.nodesByType).map(
    ([name, value]) => ({
      name,
      value: value as number,
      percentage: (((value as number) / stats.totalNodes) * 100).toFixed(1),
    }),
  );

  const domainData = Object.entries(stats.nodesByDomain)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .map(([name, value]) => ({
      name: name.replace(/_/g, " "),
      value: value as number,
    }));

  const typeColors: Record<string, string> = {
    DOMAIN: "from-blue-500 to-cyan-500",
    TASK: "from-violet-500 to-purple-500",
    SUBTASK: "from-orange-500 to-amber-500",
    ATOMIC: "from-emerald-500 to-green-500",
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">Dataset Statistics</span>
          </h1>
          <p className="text-lg text-white/50">
            Real-time analytics from {stats.totalNodes.toLocaleString()} nodes
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            {
              label: "Total Nodes",
              value: stats.totalNodes.toLocaleString(),
              icon: Database,
              color: "text-blue-400",
            },
            {
              label: "Atomic Actions",
              value: stats.atomicActions.toLocaleString(),
              icon: Zap,
              color: "text-emerald-400",
            },
            {
              label: "Domains",
              value: stats.domains,
              icon: BarChart3,
              color: "text-violet-400",
            },
            {
              label: "Unique Verbs",
              value: stats.verbs.toLocaleString(),
              icon: Cpu,
              color: "text-fuchsia-400",
            },
          ].map((metric) => (
            <div
              key={metric.label}
              className="glass rounded-2xl p-6 text-center"
            >
              <metric.icon className={`w-8 h-8 ${metric.color} mx-auto mb-3`} />
              <div className="text-3xl font-bold text-white mb-1">
                {metric.value}
              </div>
              <div className="text-sm text-white/50">{metric.label}</div>
            </div>
          ))}
        </div>

        {/* Node Types Distribution */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="glass rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-violet-400" />
              Node Type Distribution
            </h2>
            <div className="space-y-4">
              {nodeTypeData.map((item) => (
                <div key={item.name}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/80">{item.name}</span>
                    <span className="text-white/50">
                      {item.value.toLocaleString()} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${typeColors[item.name] || "from-gray-500 to-gray-600"} rounded-full transition-all duration-1000`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-violet-400" />
              Tree Depth
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-xl p-6 text-center">
                <div className="text-4xl font-bold text-violet-400 mb-2">
                  {stats.avgDepth}
                </div>
                <div className="text-sm text-white/50">Average Depth</div>
              </div>
              <div className="bg-white/5 rounded-xl p-6 text-center">
                <div className="text-4xl font-bold text-fuchsia-400 mb-2">
                  {stats.maxDepth}
                </div>
                <div className="text-sm text-white/50">Maximum Depth</div>
              </div>
            </div>
            <div className="mt-6 text-sm text-white/40 text-center">
              Hierarchical path: Domain → Task → Subtask → Atomic
            </div>
          </div>
        </div>

        {/* Top Domains */}
        <div className="glass rounded-2xl p-6 mb-12">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-violet-400" />
            Top Domains by Node Count
          </h2>
          <div className="space-y-3">
            {domainData.slice(0, 10).map((domain, idx) => {
              const maxValue = domainData[0]?.value || 1;
              const percentage = (domain.value / maxValue) * 100;

              return (
                <div key={domain.name} className="flex items-center gap-4">
                  <span className="w-6 text-sm text-white/40">{idx + 1}</span>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-white/80 capitalize">
                        {domain.name}
                      </span>
                      <span className="text-white/50">
                        {domain.value.toLocaleString()}
                      </span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Verbs */}
        <div className="glass rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-violet-400" />
            Most Common Atomic Verbs
          </h2>
          <div className="flex flex-wrap gap-2">
            {stats.topVerbs
              .slice(0, 30)
              .map((item: { verb: string; count: number }, idx: number) => (
                <span
                  key={item.verb}
                  className="px-3 py-2 rounded-lg bg-white/5 text-sm hover:bg-white/10 transition-colors cursor-default"
                  title={`${item.count.toLocaleString()} occurrences`}
                >
                  <span className="text-white/80">{item.verb}</span>
                  <span className="text-white/30 ml-2">
                    {item.count.toLocaleString()}
                  </span>
                </span>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
