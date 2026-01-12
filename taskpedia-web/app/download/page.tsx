import type { Metadata } from "next";
import Link from "next/link";
import {
  Download,
  Github,
  Terminal,
  Database,
  FileJson,
  Sparkles,
} from "lucide-react";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Download",
  description:
    "Download the TASKPEDIA dataset. Access via HuggingFace, CLI, or direct download.",
};

export default function DownloadPage() {
  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="gradient-text">Download Dataset</span>
          </h1>
          <p className="text-lg text-white/50">
            Multiple ways to access TASKPEDIA
          </p>
        </div>

        <div className="space-y-6">
          {/* HuggingFace */}
          <div className="glass rounded-2xl p-8 hover:bg-white/10 transition-all">
            <div className="flex items-start gap-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center flex-shrink-0 glow-sm">
                <Database className="w-7 h-7 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">
                  HuggingFace Hub
                </h2>
                <p className="text-white/50 mb-4">
                  Recommended for Python workflows
                </p>
                <div className="bg-black/40 rounded-xl p-4 mb-4 font-mono text-sm overflow-x-auto">
                  <code className="text-emerald-400">
                    <span className="text-white/50">from</span> datasets{" "}
                    <span className="text-white/50">import</span> load_dataset
                    {"\n"}
                    dataset = load_dataset(
                    <span className="text-amber-400">
                      "Sentient-x/taskpedia"
                    </span>
                    )
                  </code>
                </div>
                <a
                  href="https://huggingface.co/datasets/Sentient-x/taskpedia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-orange-500 text-white font-semibold hover:opacity-90 transition-opacity"
                >
                  View on HuggingFace
                  <Sparkles className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>

          {/* CLI */}
          <div className="glass rounded-2xl p-8 hover:bg-white/10 transition-all">
            <div className="flex items-start gap-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center flex-shrink-0 glow-sm">
                <Terminal className="w-7 h-7 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">
                  TASKPEDIA CLI
                </h2>
                <p className="text-white/50 mb-4">
                  Full control with command-line tools
                </p>
                <div className="bg-black/40 rounded-xl p-4 mb-4 font-mono text-sm overflow-x-auto">
                  <code className="text-emerald-400">
                    <span className="text-white/50"># Install</span>
                    {"\n"}
                    uv pip install -e .{"\n\n"}
                    <span className="text-white/50"># Download</span>
                    {"\n"}
                    taskpedia download --repo Sentient-x/taskpedia{"\n\n"}
                    <span className="text-white/50"># Explore</span>
                    {"\n"}
                    taskpedia show stats{"\n"}
                    taskpedia show tree -d 4
                  </code>
                </div>
                <Link
                  href="/docs"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 text-white font-semibold hover:opacity-90 transition-opacity"
                >
                  View Documentation
                </Link>
              </div>
            </div>
          </div>

          {/* GitHub */}
          <div className="glass rounded-2xl p-8 hover:bg-white/10 transition-all">
            <div className="flex items-start gap-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center flex-shrink-0">
                <Github className="w-7 h-7 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-2">
                  Source Code
                </h2>
                <p className="text-white/50 mb-4">
                  Generate your own dataset or contribute
                </p>
                <a
                  href="https://github.com/anthropics/taskpedia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl glass text-white font-semibold hover:bg-white/10 transition-colors"
                >
                  <Github className="w-5 h-5" />
                  View on GitHub
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="mt-12 glass rounded-2xl p-8">
          <h3 className="text-lg font-semibold text-white mb-4">
            Dataset Information
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
            <div>
              <p className="text-white/40 mb-1">License</p>
              <p className="text-white">CC BY 4.0</p>
            </div>
            <div>
              <p className="text-white/40 mb-1">Size</p>
              <p className="text-white">~50MB compressed</p>
            </div>
            <div>
              <p className="text-white/40 mb-1">Format</p>
              <p className="text-white">JSON, JSONL</p>
            </div>
            <div>
              <p className="text-white/40 mb-1">Updates</p>
              <p className="text-white">Regular</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
