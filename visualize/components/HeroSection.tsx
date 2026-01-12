import Link from 'next/link';
import { ArrowRight, Database, Zap, Globe } from 'lucide-react';

interface HeroSectionProps {
  stats: {
    totalNodes: number;
    atomicActions: number;
    domains: number;
    verbs: number;
  };
}

export function HeroSection({ stats }: HeroSectionProps) {
  return (
    <div className="relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-blue-50 to-indigo-50 opacity-70"></div>
      <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-gradient-to-bl from-primary-200 to-transparent opacity-30 blur-3xl"></div>
      <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-gradient-to-tr from-indigo-200 to-transparent opacity-30 blur-3xl"></div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-md mb-8 animate-slide-up">
            <Zap className="w-4 h-4 text-primary-600" />
            <span className="text-sm font-medium text-gray-700">
              Millions of atomic robot actions
            </span>
          </div>

          {/* Main heading */}
          <h1 className="text-5xl lg:text-7xl font-bold text-gray-900 mb-6 animate-fade-in">
            <span className="bg-gradient-to-r from-primary-600 via-blue-600 to-indigo-600 bg-clip-text text-transparent">
              TASKPEDIA
            </span>
          </h1>

          <p className="text-xl lg:text-2xl text-gray-700 mb-4 max-w-3xl mx-auto animate-slide-up animation-delay-200">
            Hierarchical Task Decomposition Dataset for Embodied AI
          </p>

          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto animate-slide-up animation-delay-400">
            Decompose human activities into atomic robot-executable actions. Perfect for VLA/VLN training with {stats.verbs.toLocaleString()}+ atomic verbs across {stats.domains}+ domains.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-slide-up animation-delay-600">
            <Link
              href="/explore"
              className="group flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              <span>Explore Dataset</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/download"
              className="flex items-center space-x-2 px-8 py-4 bg-white/80 backdrop-blur-sm text-gray-900 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 border border-gray-200"
            >
              <Database className="w-5 h-5" />
              <span>Download</span>
            </Link>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                {stats.totalNodes.toLocaleString()}+
              </div>
              <div className="text-sm text-gray-600 font-medium">Total Nodes</div>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                {stats.atomicActions.toLocaleString()}+
              </div>
              <div className="text-sm text-gray-600 font-medium">Atomic Actions</div>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                {stats.verbs.toLocaleString()}+
              </div>
              <div className="text-sm text-gray-600 font-medium">Atomic Verbs</div>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-md hover:shadow-lg transition-shadow">
              <div className="text-3xl lg:text-4xl font-bold text-primary-600 mb-2">
                {stats.domains}+
              </div>
              <div className="text-sm text-gray-600 font-medium">Domains</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
