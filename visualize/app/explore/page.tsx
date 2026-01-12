import { Suspense } from 'react';
import type { Metadata } from 'next';
import { SearchInterface } from '@/components/SearchInterface';

export const metadata: Metadata = {
  title: 'Explore Tasks',
  description: 'Search and explore millions of atomic robot-executable actions across 35+ domains in the TASKPEDIA dataset.',
  openGraph: {
    title: 'Explore Tasks - TASKPEDIA',
    description: 'Search and explore millions of atomic robot-executable actions',
  },
};

export default function ExplorePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Explore the Dataset
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Search through millions of hierarchical task decompositions and atomic actions
          </p>
        </div>

        <Suspense fallback={<div className="h-96 skeleton rounded-2xl" />}>
          <SearchInterface />
        </Suspense>
      </div>
    </div>
  );
}
