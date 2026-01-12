import Link from 'next/link';
import { Download, Github, BookOpen, Sparkles } from 'lucide-react';

export function CTASection() {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary-600 via-blue-600 to-indigo-700 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 bg-grid-white/10 bg-grid-pattern opacity-20"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>

      <div className="max-w-4xl mx-auto text-center relative z-10">
        <div className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
          <Sparkles className="w-4 h-4 text-white" />
          <span className="text-sm font-medium text-white">
            Open Source & Free to Use
          </span>
        </div>

        <h2 className="text-4xl lg:text-5xl font-bold text-white mb-6">
          Ready to build the future of embodied AI?
        </h2>

        <p className="text-xl text-blue-100 mb-12 max-w-2xl mx-auto">
          Download TASKPEDIA today and accelerate your robot learning research with millions of atomic actions.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/download"
            className="group flex items-center space-x-2 px-8 py-4 bg-white text-primary-700 rounded-xl font-semibold text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-200"
          >
            <Download className="w-5 h-5 group-hover:animate-bounce" />
            <span>Download Dataset</span>
          </Link>

          <a
            href="https://github.com/anthropics/taskpedia"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-8 py-4 bg-white/10 backdrop-blur-sm text-white rounded-xl font-semibold text-lg border-2 border-white/20 hover:bg-white/20 transition-all duration-200"
          >
            <Github className="w-5 h-5" />
            <span>View on GitHub</span>
          </a>

          <Link
            href="/docs"
            className="flex items-center space-x-2 px-8 py-4 bg-transparent text-white rounded-xl font-semibold text-lg border-2 border-white/30 hover:bg-white/10 transition-all duration-200"
          >
            <BookOpen className="w-5 h-5" />
            <span>Documentation</span>
          </Link>
        </div>

        <p className="mt-8 text-sm text-blue-200">
          Licensed under CC BY 4.0 • Over 1M+ atomic actions • Updated regularly
        </p>
      </div>
    </section>
  );
}
