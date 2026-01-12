'use client';

import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Database, Layers, Activity } from 'lucide-react';
import type { DatasetStats } from '@/lib/data';

interface StatsDashboardProps {
  stats: DatasetStats;
}

export function StatsDashboard({ stats }: StatsDashboardProps) {
  const nodeTypeData = Object.entries(stats.nodesByType).map(([name, value]) => ({
    name,
    value,
  }));

  const domainData = Object.entries(stats.nodesByDomain)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([name, value]) => ({
      name: name.replace(/_/g, ' '),
      value,
    }));

  const verbData = stats.topVerbs.map(v => ({
    name: v.verb,
    count: v.count,
  }));

  const COLORS = ['#3b82f6', '#8b5cf6', '#f97316', '#10b981', '#ef4444', '#f59e0b', '#06b6d4', '#ec4899'];

  return (
    <div className="space-y-8">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={Database}
          label="Total Nodes"
          value={stats.totalNodes.toLocaleString()}
          color="from-blue-500 to-blue-600"
        />
        <MetricCard
          icon={Activity}
          label="Atomic Actions"
          value={stats.atomicActions.toLocaleString()}
          color="from-green-500 to-green-600"
        />
        <MetricCard
          icon={Layers}
          label="Domains"
          value={stats.domains.toString()}
          color="from-purple-500 to-purple-600"
        />
        <MetricCard
          icon={TrendingUp}
          label="Unique Verbs"
          value={stats.verbs.toLocaleString()}
          color="from-orange-500 to-orange-600"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Node Type Distribution */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Node Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={nodeTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {nodeTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => value.toLocaleString()} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Tree Depth Info */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Hierarchy Depth</h3>
          <div className="space-y-6">
            <div className="flex items-center justify-between p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl">
              <div>
                <p className="text-sm text-gray-600 font-medium mb-1">Average Depth</p>
                <p className="text-4xl font-bold text-blue-600">{stats.avgDepth.toFixed(1)}</p>
              </div>
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                <Layers className="w-10 h-10 text-white" />
              </div>
            </div>
            <div className="flex items-center justify-between p-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl">
              <div>
                <p className="text-sm text-gray-600 font-medium mb-1">Maximum Depth</p>
                <p className="text-4xl font-bold text-purple-600">{stats.maxDepth}</p>
              </div>
              <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-10 h-10 text-white" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6">
        {/* Top Domains */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Top 10 Domains by Task Count</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={domainData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={150} />
              <Tooltip formatter={(value: number) => value.toLocaleString()} />
              <Legend />
              <Bar dataKey="value" name="Tasks" fill="#3b82f6" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Verbs */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Most Common Atomic Verbs</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={verbData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => value.toLocaleString()} />
              <Legend />
              <Bar dataKey="count" name="Occurrences" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="bg-gradient-to-br from-primary-600 to-indigo-700 rounded-2xl shadow-lg p-8 text-white">
        <h3 className="text-2xl font-bold mb-6">Dataset Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-blue-200 text-sm mb-1">Coverage</p>
            <p className="text-3xl font-bold">{stats.domains}+ Domains</p>
            <p className="text-blue-200 text-sm mt-2">Spanning work and life activities</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm mb-1">Granularity</p>
            <p className="text-3xl font-bold">{stats.verbs.toLocaleString()}+ Verbs</p>
            <p className="text-blue-200 text-sm mt-2">Atomic robot-executable actions</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm mb-1">Scale</p>
            <p className="text-3xl font-bold">{(stats.totalNodes / 1000000).toFixed(1)}M+ Nodes</p>
            <p className="text-blue-200 text-sm mt-2">Hierarchical task decompositions</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  color
}: {
  icon: any;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 bg-gradient-to-br ${color} rounded-xl flex items-center justify-center shadow-md`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-sm text-gray-600 font-medium">{label}</p>
    </div>
  );
}
