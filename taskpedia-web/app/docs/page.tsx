import type { Metadata } from "next";
import {
  BookOpen,
  Terminal,
  Database,
  Zap,
  Code,
  GitBranch,
} from "lucide-react";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Documentation",
  description: "Learn how to use TASKPEDIA dataset for embodied AI training.",
};

export default function DocsPage() {
  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">Documentation</span>
          </h1>
          <p className="text-lg text-white/50">
            Everything you need to integrate TASKPEDIA
          </p>
        </div>

        {/* Quick Start */}
        <section className="glass rounded-2xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Zap className="w-6 h-6 text-violet-400" />
            Quick Start
          </h2>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">
                Installation
              </h3>
              <div className="bg-black/40 rounded-xl p-4 font-mono text-sm overflow-x-auto">
                <code className="text-emerald-400">
                  <span className="text-white/50"># Using pip</span>
                  {"\n"}
                  pip install datasets{"\n\n"}
                  <span className="text-white/50"># Or clone for CLI</span>
                  {"\n"}
                  git clone https://github.com/anthropics/taskpedia{"\n"}
                  cd taskpedia && uv pip install -e .
                </code>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-3">
                Load Dataset
              </h3>
              <div className="bg-black/40 rounded-xl p-4 font-mono text-sm overflow-x-auto">
                <code className="text-emerald-400">
                  <span className="text-white/50">from</span> datasets{" "}
                  <span className="text-white/50">import</span> load_dataset
                  {"\n\n"}
                  dataset = load_dataset(
                  <span className="text-amber-400">"Sentient-x/taskpedia"</span>
                  ){"\n\n"}
                  <span className="text-white/50"># Explore</span>
                  {"\n"}
                  <span className="text-white/50">for</span> task{" "}
                  <span className="text-white/50">in</span> dataset[
                  <span className="text-amber-400">"train"</span>]:{"\n"}
                  {"    "}print(f
                  <span className="text-amber-400">
                    "&#123;task['name']&#125; - &#123;task['node_type']&#125;"
                  </span>
                  )
                </code>
              </div>
            </div>
          </div>
        </section>

        {/* Node Types */}
        <section className="glass rounded-2xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <GitBranch className="w-6 h-6 text-violet-400" />
            Node Types
          </h2>

          <div className="space-y-4">
            {[
              {
                type: "DOMAIN",
                desc: "Top-level categories",
                example: "work_healthcare, life_household",
                color: "from-blue-500 to-cyan-500",
              },
              {
                type: "TASK",
                desc: "High-level tasks",
                example: "patient_care, cooking",
                color: "from-violet-500 to-purple-500",
              },
              {
                type: "SUBTASK",
                desc: "Intermediate steps",
                example: "take_vitals, prepare_ingredients",
                color: "from-orange-500 to-amber-500",
              },
              {
                type: "ATOMIC",
                desc: "Robot-executable actions",
                example: "grasp, move_to, release",
                color: "from-emerald-500 to-green-500",
              },
            ].map((item) => (
              <div
                key={item.type}
                className="flex items-start gap-4 p-4 bg-white/5 rounded-xl"
              >
                <span
                  className={`px-3 py-1 rounded-lg text-sm font-semibold bg-gradient-to-r ${item.color} text-white`}
                >
                  {item.type}
                </span>
                <div>
                  <p className="text-white font-medium">{item.desc}</p>
                  <p className="text-sm text-white/50 mt-1">
                    e.g., {item.example}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CLI Commands */}
        <section className="glass rounded-2xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Terminal className="w-6 h-6 text-violet-400" />
            CLI Commands
          </h2>

          <div className="bg-black/40 rounded-xl p-4 font-mono text-sm overflow-x-auto">
            <code className="text-emerald-400">
              <span className="text-white/50"># View statistics</span>
              {"\n"}
              taskpedia show stats{"\n\n"}
              <span className="text-white/50"># Browse tree</span>
              {"\n"}
              taskpedia show tree -d 4{"\n\n"}
              <span className="text-white/50"># Search</span>
              {"\n"}
              taskpedia show search "grasp"{"\n\n"}
              <span className="text-white/50"># Export</span>
              {"\n"}
              taskpedia export -f jsonl{"\n\n"}
              <span className="text-white/50"># Generate more</span>
              {"\n"}
              taskpedia generate -n 100000
            </code>
          </div>
        </section>

        {/* Data Schema */}
        <section className="glass rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Code className="w-6 h-6 text-violet-400" />
            Data Schema
          </h2>

          <div className="bg-black/40 rounded-xl p-4 font-mono text-sm overflow-x-auto">
            <code className="text-emerald-400">
              {"{"}
              {"\n"}
              {"  "}
              <span className="text-amber-400">"id"</span>:{" "}
              <span className="text-cyan-400">
                "work_healthcare/nursing/take_vitals"
              </span>
              ,{"\n"}
              {"  "}
              <span className="text-amber-400">"name"</span>:{" "}
              <span className="text-cyan-400">"take patient vitals"</span>,
              {"\n"}
              {"  "}
              <span className="text-amber-400">"node_type"</span>:{" "}
              <span className="text-cyan-400">"SUBTASK"</span>,{"\n"}
              {"  "}
              <span className="text-amber-400">"parent_id"</span>:{" "}
              <span className="text-cyan-400">"work_healthcare/nursing"</span>,
              {"\n"}
              {"  "}
              <span className="text-amber-400">"children_ids"</span>: [{"\n"}
              {"    "}
              <span className="text-cyan-400">
                "work_healthcare/nursing/take_vitals/grasp_thermometer"
              </span>
              ,{"\n"}
              {"    "}
              <span className="text-cyan-400">
                "work_healthcare/nursing/take_vitals/measure_temperature"
              </span>
              {"\n"}
              {"  "}]{"\n"}
              {"}"}
            </code>
          </div>
        </section>
      </div>
    </div>
  );
}
