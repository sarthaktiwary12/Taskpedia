'use client';

import { useState, useMemo } from 'react';
import { Search, Filter, X, Zap, ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface Node {
  id: string;
  name: string;
  node_type: string;
  parent_id?: string;
  children_ids?: string[];
}

interface ExploreClientProps {
  domains: Node[];
  samples: Node[];
}

export function ExploreClient({ domains, samples }: ExploreClientProps) {
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [allNodes, setAllNodes] = useState<Node[]>([...domains, ...samples]);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load full manifest on client side for search
  const loadFullManifest = async () => {
    if (isLoaded) return;
    try {
      const res = await fetch('/data/manifest.json');
      const manifest = await res.json();
      setAllNodes(Object.values(manifest));
      setIsLoaded(true);
    } catch (e) {
      console.error('Failed to load manifest:', e);
    }
  };

  const filteredNodes = useMemo(() => {
    let results = allNodes;

    if (query.trim()) {
      const q = query.toLowerCase();
      results = results.filter(
        (node) =>
          node.name?.toLowerCase().includes(q) ||
          node.id?.toLowerCase().includes(q)
      );
    }

    if (typeFilter !== 'all') {
      results = results.filter(
        (node) => node.node_type?.toUpperCase() === typeFilter
      );
    }

    return results.slice(0, 100);
  }, [allNodes, query, typeFilter]);

  const typeColors: Record<string, string> = {
    DOMAIN: 'from-blue-500 to-cyan-500',
    TASK: 'from-violet-500 to-purple-500',
    SUBTASK: 'from-orange-500 to-amber-500',
    ATOMIC: 'from-emerald-500 to-green-500',
  };

  return (
    <div className="space-y-6">
      {/* Search Box */}
      <div className="glass rounded-2xl p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                loadFullManifest();
              }}
              onFocus={loadFullManifest}
              placeholder="Search tasks, actions, or domains..."
              className="w-full pl-12 pr-4 py-4 bg-white/5 rounded-xl border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-violet-500/50 focus:bg-white/10 transition-all"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="flex gap-2">
            {['all', 'DOMAIN', 'TASK', 'SUBTASK', 'ATOMIC'].map((type) => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  typeFilter === type
                    ? 'bg-violet-600 text-white'
                    : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
                }`}
              >
                {type === 'all' ? 'All' : type}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between text-sm text-white/50">
        <span>
          {filteredNodes.length} results
          {filteredNodes.length === 100 && ' (showing first 100)'}
        </span>
        {!isLoaded && (
          <span className="text-violet-400">Click search to load full dataset</span>
        )}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredNodes.map((node) => {
          const nodeType = node.node_type?.toUpperCase() || 'UNKNOWN';
          const gradient = typeColors[nodeType] || 'from-gray-500 to-gray-600';

          return (
            <Link
              key={node.id}
              href={`/node/${encodeURIComponent(node.id)}`}
              className="glass rounded-xl p-5 hover:bg-white/10 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r ${gradient} text-white`}
                >
                  {nodeType}
                </span>
                <ChevronRight className="w-5 h-5 text-white/30 group-hover:text-white/60 group-hover:translate-x-1 transition-all" />
              </div>

              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-violet-300 transition-colors">
                {node.name}
              </h3>

              <p className="text-sm text-white/40 font-mono truncate">{node.id}</p>

              {node.children_ids && node.children_ids.length > 0 && (
                <div className="mt-3 text-xs text-white/30">
                  {node.children_ids.length} children
                </div>
              )}
            </Link>
          );
        })}
      </div>

      {filteredNodes.length === 0 && (
        <div className="text-center py-16 glass rounded-2xl">
          <Search className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <p className="text-white/50">No results found</p>
          <p className="text-sm text-white/30 mt-2">Try different keywords</p>
        </div>
      )}
    </div>
  );
}
