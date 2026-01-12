import type { Metadata } from 'next';
import { Download, Github, Terminal, FileJson, Database } from 'lucide-react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Download',
  description: 'Download the TASKPEDIA dataset in multiple formats. Access via HuggingFace, CLI, or direct download.',
  openGraph: {
    title: 'Download - TASKPEDIA',
    description: 'Download the TASKPEDIA dataset in multiple formats',
  },
};

export default function DownloadPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Download TASKPEDIA
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Access the complete hierarchical task decomposition dataset
          </p>
        </div>

        <div className="space-y-6">
          {/* HuggingFace */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                <Database className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  HuggingFace Hub (Recommended)
                </h2>
                <p className="text-gray-600 mb-4">
                  The easiest way to access TASKPEDIA. Integrates seamlessly with Python workflows.
                </p>
                <div className="bg-gray-900 rounded-lg p-4 mb-4">
                  <code className="text-green-400 text-sm font-mono">
                    pip install datasets<br/>
                    <br/>
                    from datasets import load_dataset<br/>
                    dataset = load_dataset("Sentient-x/taskpedia")
                  </code>
                </div>
                <a
                  href="https://huggingface.co/datasets/Sentient-x/taskpedia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  <span>View on HuggingFace</span>
                  <span>→</span>
                </a>
              </div>
            </div>
          </div>

          {/* CLI */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                <Terminal className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  TASKPEDIA CLI
                </h2>
                <p className="text-gray-600 mb-4">
                  Install the official CLI to download, explore, and generate tasks locally.
                </p>
                <div className="bg-gray-900 rounded-lg p-4 mb-4">
                  <code className="text-green-400 text-sm font-mono">
                    # Install CLI<br/>
                    uv pip install -e .<br/>
                    <br/>
                    # Download dataset<br/>
                    taskpedia download --repo Sentient-x/taskpedia<br/>
                    <br/>
                    # Explore<br/>
                    taskpedia show stats<br/>
                    taskpedia show tree -d 4
                  </code>
                </div>
                <Link
                  href="/docs"
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  <span>View Documentation</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          </div>

          {/* Direct Download */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                <FileJson className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Direct Download
                </h2>
                <p className="text-gray-600 mb-4">
                  Download the dataset in various formats for offline use.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="font-semibold text-gray-900 mb-2">JSON</p>
                    <p className="text-sm text-gray-600 mb-3">Complete hierarchy</p>
                    <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                      Download →
                    </button>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="font-semibold text-gray-900 mb-2">JSONL</p>
                    <p className="text-sm text-gray-600 mb-3">Line-delimited</p>
                    <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                      Download →
                    </button>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="font-semibold text-gray-900 mb-2">CSV</p>
                    <p className="text-sm text-gray-600 mb-3">Flat format</p>
                    <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                      Download →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* GitHub */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
            <div className="flex items-start space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-gray-700 to-gray-900 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                <Github className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Source Code
                </h2>
                <p className="text-gray-600 mb-4">
                  Access the full source code, contribute, or generate your own dataset.
                </p>
                <a
                  href="https://github.com/anthropics/taskpedia"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-gray-700 to-gray-900 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
                >
                  <Github className="w-5 h-5" />
                  <span>View on GitHub</span>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-gradient-to-br from-primary-600 to-indigo-700 rounded-2xl shadow-lg p-8 text-white">
          <h3 className="text-2xl font-bold mb-4">Dataset Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <p className="font-semibold mb-2">License</p>
              <p className="text-blue-100">CC BY 4.0 - Free for research and commercial use</p>
            </div>
            <div>
              <p className="font-semibold mb-2">Size</p>
              <p className="text-blue-100">~500MB compressed, ~2GB uncompressed</p>
            </div>
            <div>
              <p className="font-semibold mb-2">Format</p>
              <p className="text-blue-100">JSON, JSONL, CSV, YAML</p>
            </div>
            <div>
              <p className="font-semibold mb-2">Updates</p>
              <p className="text-blue-100">Regular updates with new tasks and domains</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
