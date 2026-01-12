'use client';

import { Activity, Box, GitBranch, Layers } from 'lucide-react';
import type { DatasetStats } from '@/lib/data';

interface StatsOverviewProps {
  stats: DatasetStats;
}

export function StatsOverview({ stats }: StatsOverviewProps) {
  const statCards = [
    {
      icon: Box,
      label: 'Node Types',
      data: Object.entries(stats.nodesByType).map(([type, count]) => ({
        name: type,
        value: count,
        percentage: ((count / stats.totalNodes) * 100).toFixed(1),
      })),
      color: 'from-blue-500 to-blue-600',
    },
    {
      icon: GitBranch,
      label: 'Tree Depth',
      data: [
        { name: 'Average', value: stats.avgDepth.toFixed(1), unit: 'levels' },
        { name: 'Maximum', value: stats.maxDepth, unit: 'levels' },
      ],
      color: 'from-green-500 to-green-600',
    },
    {
      icon: Activity,
      label: 'Top Verbs',
      data: stats.topVerbs.slice(0, 5).map(v => ({
        name: v.verb,
        value: v.count.toLocaleString(),
        percentage: ((v.count / stats.atomicActions) * 100).toFixed(1),
      })),
      color: 'from-purple-500 to-purple-600',
    },
    {
      icon: Layers,
      label: 'Top Domains',
      data: Object.entries(stats.nodesByDomain)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([domain, count]) => ({
          name: domain.replace(/_/g, ' '),
          value: count.toLocaleString(),
          percentage: ((count / stats.totalNodes) * 100).toFixed(1),
        })),
      color: 'from-orange-500 to-orange-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.label}
            className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow border border-gray-100"
          >
            <div className="flex items-center space-x-3 mb-4">
              <div className={`w-10 h-10 bg-gradient-to-br ${card.color} rounded-lg flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900">{card.label}</h3>
            </div>

            <div className="space-y-3">
              {card.data.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 capitalize">
                    {item.name}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-semibold text-gray-900">
                      {item.value}
                      {(item as any).unit && ` ${(item as any).unit}`}
                    </span>
                    {(item as any).percentage && (
                      <span className="text-xs text-gray-500">
                        ({(item as any).percentage}%)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
