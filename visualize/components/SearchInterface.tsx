'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, X, ChevronDown } from 'lucide-react';
import { TaskCard } from './TaskCard';
import type { TaskNode } from '@/lib/data';

export function SearchInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<TaskNode[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState({
    nodeType: 'all',
    domain: 'all',
  });
  const [showFilters, setShowFilters] = useState(false);

  const nodeTypes = ['all', 'DOMAIN', 'TASK', 'SUBTASK', 'ATOMIC'];
  const domains = ['all', 'work_healthcare', 'work_manufacturing', 'work_construction', 'life_household'];

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q);
    }
  }, []);

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}&limit=100`);
      const data = await response.json();
      let filteredResults = data.results || [];

      // Apply filters
      if (filters.nodeType !== 'all') {
        filteredResults = filteredResults.filter((r: TaskNode) => r.node_type === filters.nodeType);
      }
      if (filters.domain !== 'all') {
        filteredResults = filteredResults.filter((r: TaskNode) => r.id.startsWith(filters.domain));
      }

      setResults(filteredResults);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const clearFilters = () => {
    setFilters({ nodeType: 'all', domain: 'all' });
  };

  useEffect(() => {
    if (query) {
      performSearch(query);
    }
  }, [filters]);

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search tasks, actions, verbs, or domains..."
                className="w-full pl-12 pr-4 py-3 bg-gray-50 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
              />
            </div>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-medium transition-colors ${
                showFilters
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="w-5 h-5" />
              <span>Filters</span>
              <ChevronDown
                className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`}
              />
            </button>
            <button
              type="submit"
              className="px-8 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-semibold hover:shadow-lg transition-shadow"
            >
              Search
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="pt-4 border-t border-gray-200 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Node Type
                  </label>
                  <select
                    value={filters.nodeType}
                    onChange={(e) => setFilters({ ...filters, nodeType: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {nodeTypes.map((type) => (
                      <option key={type} value={type}>
                        {type === 'all' ? 'All Types' : type}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domain
                  </label>
                  <select
                    value={filters.domain}
                    onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-50 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    {domains.map((domain) => (
                      <option key={domain} value={domain}>
                        {domain === 'all' ? 'All Domains' : domain.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {(filters.nodeType !== 'all' || filters.domain !== 'all') && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
                >
                  <X className="w-4 h-4" />
                  <span>Clear filters</span>
                </button>
              )}
            </div>
          )}
        </form>
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Searching...</p>
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {results.length} {results.length === 1 ? 'result' : 'results'} found
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      ) : query ? (
        <div className="text-center py-12 bg-white rounded-2xl shadow-lg border border-gray-200">
          <p className="text-gray-600">No results found for "{query}"</p>
          <p className="text-sm text-gray-500 mt-2">Try different keywords or clear your filters</p>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-2xl shadow-lg border border-gray-200">
          <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Enter a search query to explore the dataset</p>
        </div>
      )}
    </div>
  );
}
