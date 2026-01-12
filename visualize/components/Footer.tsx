import Link from 'next/link';
import { Database, Github, Twitter, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-gray-300 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">TASKPEDIA</span>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Hierarchical task decomposition dataset for embodied AI training
            </p>
            <div className="flex space-x-4">
              <a href="https://github.com/anthropics/taskpedia" target="_blank" rel="noopener noreferrer" className="hover:text-primary-400 transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="https://twitter.com/sentientx" target="_blank" rel="noopener noreferrer" className="hover:text-primary-400 transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="mailto:contact@taskpedia.ai" className="hover:text-primary-400 transition-colors">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Dataset */}
          <div>
            <h3 className="text-white font-semibold mb-4">Dataset</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/explore" className="hover:text-primary-400 transition-colors">Explore Tasks</Link></li>
              <li><Link href="/dataset" className="hover:text-primary-400 transition-colors">Browse Dataset</Link></li>
              <li><Link href="/stats" className="hover:text-primary-400 transition-colors">Statistics</Link></li>
              <li><Link href="/download" className="hover:text-primary-400 transition-colors">Download</Link></li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-white font-semibold mb-4">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/docs" className="hover:text-primary-400 transition-colors">Documentation</Link></li>
              <li><Link href="/docs/api" className="hover:text-primary-400 transition-colors">API Reference</Link></li>
              <li><Link href="/docs/getting-started" className="hover:text-primary-400 transition-colors">Getting Started</Link></li>
              <li><a href="https://huggingface.co/datasets/Sentient-x/taskpedia" target="_blank" rel="noopener noreferrer" className="hover:text-primary-400 transition-colors">HuggingFace</a></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/license" className="hover:text-primary-400 transition-colors">License</Link></li>
              <li><Link href="/terms" className="hover:text-primary-400 transition-colors">Terms of Use</Link></li>
              <li><Link href="/privacy" className="hover:text-primary-400 transition-colors">Privacy Policy</Link></li>
              <li><Link href="/citation" className="hover:text-primary-400 transition-colors">Citation</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center text-sm">
          <p className="text-gray-400">
            © {new Date().getFullYear()} TASKPEDIA. Licensed under CC BY 4.0.
          </p>
          <p className="text-gray-400 mt-2 md:mt-0">
            Built for the embodied AI research community
          </p>
        </div>
      </div>
    </footer>
  );
}
