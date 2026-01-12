import { Suspense } from 'react';
import type { Metadata } from 'next';
import { getDatasetStats } from '@/lib/data';
import { StatsDashboard } from '@/components/StatsDashboard';

export const metadata: Metadata = {
  title: 'Statistics',
  description: 'Comprehensive statistics and analytics for the TASKPEDIA hierarchical task decomposition dataset.',
  openGraph: {
    title: 'Statistics - TASKPEDIA',
    description: 'Comprehensive statistics and analytics for the TASKPEDIA dataset',
  },
};

export const revalidate = 3600;

export default async function StatsPage() {
  const stats = await getDatasetStats();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Dataset Statistics
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive analytics and insights into the TASKPEDIA dataset
          </p>
        </div>

        <Suspense fallback={<div className="h-96 skeleton rounded-2xl" />}>
          <StatsDashboard stats={stats} />
        </Suspense>
      </div>
    </div>
  );
}
