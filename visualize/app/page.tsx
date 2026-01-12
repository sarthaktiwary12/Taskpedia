import Link from "next/link";
import {
  ArrowRight,
  Zap,
  Database,
  GitBranch,
  Cpu,
  ChevronRight,
} from "lucide-react";
import fs from "fs";
import path from "path";

// SSG - generate at build time
export const dynamic = "force-static";
export const revalidate = 3600;

async function getStats() {
  try {
    const statsPath = path.join(process.cwd(), "public", "data", "stats.json");
    const data = fs.readFileSync(statsPath, "utf-8");
    return JSON.parse(data);
  } catch {
    return {
      totalNodes: 45365,
      atomicActions: 38397,
      domains: 35,
      verbs: 1322,
      avgDepth: 4.45,
      maxDepth: 8,
    };
  }
}

export default async function HomePage() {
  const stats = await getStats();

  return (
    <div className="relative">
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center px-4 overflow-hidden">
        {/* Floating orbs */}
        <div
          className="absolute top-20 left-20 w-2 h-2 bg-violet-400 rounded-full animate-float"
          style={{ animationDelay: "0s" }}
        />
        <div
          className="absolute top-40 right-32 w-3 h-3 bg-fuchsia-400 rounded-full animate-float"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute bottom-32 left-1/4 w-2 h-2 bg-purple-400 rounded-full animate-float"
          style={{ animationDelay: "2s" }}
        />

        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8">
            <Zap className="w-4 h-4 text-violet-400" />
            <span className="text-sm text-white/80">
              {stats.totalNodes.toLocaleString()}+ hierarchical task nodes
            </span>
          </div>

          {/* Main title */}
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-6">
            <span className="gradient-text animate-gradient bg-gradient-to-r from-violet-400 via-fuchsia-400 to-violet-400">
              TASKPEDIA
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-white/60 max-w-3xl mx-auto mb-4">
            Hierarchical Task Decomposition for Embodied AI
          </p>

          <p className="text-lg text-white/40 max-w-2xl mx-auto mb-12">
            Decompose human activities into atomic robot-executable actions.
            Built for VLA/VLN training with {stats.verbs.toLocaleString()}+
            verbs across {stats.domains} domains.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
            <Link
              href="/explore"
              className="group flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold text-lg glow hover:opacity-90 transition-all"
            >
              Explore Dataset
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/download"
              className="flex items-center gap-2 px-8 py-4 rounded-xl glass text-white font-semibold text-lg hover:bg-white/10 transition-colors"
            >
              <Database className="w-5 h-5" />
              Download
            </Link>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              {
                label: "Total Nodes",
                value: stats.totalNodes.toLocaleString(),
                icon: Database,
              },
              {
                label: "Atomic Actions",
                value: stats.atomicActions.toLocaleString(),
                icon: Zap,
              },
              {
                label: "Unique Verbs",
                value: stats.verbs.toLocaleString(),
                icon: Cpu,
              },
              { label: "Max Depth", value: stats.maxDepth, icon: GitBranch },
            ].map((stat) => (
              <div
                key={stat.label}
                className="glass rounded-2xl p-6 text-center hover:bg-white/10 transition-colors group"
              >
                <stat.icon className="w-6 h-6 text-violet-400 mx-auto mb-3 group-hover:scale-110 transition-transform" />
                <div className="text-3xl font-bold text-white mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-white/50">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-32 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              <span className="gradient-text">Built for Robot Learning</span>
            </h2>
            <p className="text-lg text-white/50 max-w-2xl mx-auto">
              Every task decomposed into atomic, robot-executable primitives
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title: "Hierarchical Structure",
                description:
                  "Domain → Task → Subtask → Atomic. Navigate from high-level goals to executable primitives.",
                gradient: "from-violet-500 to-purple-500",
              },
              {
                title: "Atomic Actions",
                description:
                  "grasp, move_to, release, inspect, pour, cut. Every action a robot can physically execute.",
                gradient: "from-purple-500 to-fuchsia-500",
              },
              {
                title: "35+ Domains",
                description:
                  "Healthcare, manufacturing, household, food prep. Real-world tasks from O*NET and life activities.",
                gradient: "from-fuchsia-500 to-pink-500",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="glass rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 group"
              >
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform glow-sm`}
                >
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-white/50 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="glass rounded-3xl p-12 md:p-16 text-center relative overflow-hidden">
            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 to-fuchsia-600/20 pointer-events-none" />

            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                <span className="gradient-text">Start Building</span>
              </h2>
              <p className="text-lg text-white/60 mb-8 max-w-xl mx-auto">
                Download the dataset and accelerate your embodied AI research
                today.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/download"
                  className="px-8 py-4 rounded-xl bg-white text-black font-semibold hover:bg-white/90 transition-colors"
                >
                  Get Started
                </Link>
                <a
                  href="https://huggingface.co/datasets/Sentient-x/taskpedia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-8 py-4 rounded-xl glass text-white font-semibold hover:bg-white/10 transition-colors"
                >
                  HuggingFace
                  <ChevronRight className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-white/40 text-sm">
            © {new Date().getFullYear()} TASKPEDIA. Licensed under CC BY 4.0.
          </div>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/anthropics/taskpedia"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/40 hover:text-white transition-colors text-sm"
            >
              GitHub
            </a>
            <a
              href="https://huggingface.co/datasets/Sentient-x/taskpedia"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/40 hover:text-white transition-colors text-sm"
            >
              HuggingFace
            </a>
            <Link
              href="/docs"
              className="text-white/40 hover:text-white transition-colors text-sm"
            >
              Documentation
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
