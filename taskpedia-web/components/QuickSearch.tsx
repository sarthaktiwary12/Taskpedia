'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, X, ChevronRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { debounce } from '@/lib/utils';

interface SearchResult {
  id: string;
  name: string;
  node_type: string;
  domain?: string;
}

export function QuickSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const searchTasks = useCallback(
    debounce(async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
        const data = await response.json();
        setResults(data.results || []);
      } catch (error) {
        console.error('Search error:', error);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    searchTasks(query);
  }, [query, searchTasks]);

  const handleSelect = (nodeId: string) => {
    router.push(`/node/${encodeURIComponent(nodeId)}`);
    setQuery('');
    setIsOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/explore?q=${encodeURIComponent(query)}`);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            placeholder="Search tasks, actions, or domains..."
            className="w-full pl-12 pr-12 py-4 bg-white rounded-2xl shadow-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
          />
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setResults([]);
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </form>

      {/* Search Results Dropdown */}
      {isOpen && (query || results.length > 0) && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 w-full bg-white rounded-2xl shadow-2xl border border-gray-200 max-h-96 overflow-y-auto z-20">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="inline-block w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : results.length > 0 ? (
              <div className="py-2">
                {results.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => handleSelect(result.id)}
                    className="w-full px-4 py-3 hover:bg-gray-50 flex items-center justify-between group transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          result.node_type === 'ATOMIC'
                            ? 'bg-green-100 text-green-700'
                            : result.node_type === 'DOMAIN'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {result.node_type}
                      </span>
                      <div className="text-left">
                        <div className="font-medium text-gray-900">{result.name}</div>
                        {result.domain && (
                          <div className="text-xs text-gray-500">{result.domain}</div>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" />
                  </button>
                ))}
              </div>
            ) : query.trim() ? (
              <div className="p-8 text-center text-gray-500">
                No results found for "{query}"
              </div>
            ) : null}

            {query.trim() && (
              <div className="border-t border-gray-200 p-3 bg-gray-50">
                <button
                  onClick={handleSubmit}
                  className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm"
                >
                  View all results for "{query}"
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
