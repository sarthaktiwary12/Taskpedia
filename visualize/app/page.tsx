import { Suspense } from 'react';
import { HeroSection } from '@/components/HeroSection';
import { StatsOverview } from '@/components/StatsOverview';
import { FeaturedDomains } from '@/components/FeaturedDomains';
import { QuickSearch } from '@/components/QuickSearch';
import { CTASection } from '@/components/CTASection';
import { getDatasetStats } from '@/lib/data';

export const revalidate = 3600; // Revalidate every hour

export default async function HomePage() {
  const stats = await getDatasetStats();

  return (
    <div className="relative">
      {/* Hero Section */}
      <HeroSection stats={stats} />

      {/* Quick Search */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <Suspense fallback={<div className="h-32 skeleton rounded-lg" />}>
          <QuickSearch />
        </Suspense>
      </section>

      {/* Stats Overview */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
            Dataset Statistics
          </h2>
          <StatsOverview stats={stats} />
        </div>
      </section>

      {/* Featured Domains */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Explore by Domain
        </h2>
        <Suspense fallback={<div className="h-96 skeleton rounded-lg" />}>
          <FeaturedDomains />
        </Suspense>
      </section>

      {/* CTA Section */}
      <CTASection />
    </div>
  );
}
