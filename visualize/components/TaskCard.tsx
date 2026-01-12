import Link from 'next/link';
import { ChevronRight, Zap } from 'lucide-react';
import type { TaskNode } from '@/lib/data';
import { getNodeTypeColor } from '@/lib/utils';

interface TaskCardProps {
  task: TaskNode;
}

export function TaskCard({ task }: TaskCardProps) {
  const color = getNodeTypeColor(task.node_type);
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    purple: 'bg-purple-100 text-purple-700 border-purple-200',
    orange: 'bg-orange-100 text-orange-700 border-orange-200',
    green: 'bg-green-100 text-green-700 border-green-200',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
  };

  return (
    <Link
      href={`/node/${encodeURIComponent(task.id)}`}
      className="group block bg-white rounded-xl p-5 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-200 hover:border-primary-300"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
              colorClasses[color as keyof typeof colorClasses]
            }`}
          >
            {task.node_type}
          </span>
          {task.node_type === 'ATOMIC' && (
            <Zap className="w-4 h-4 text-green-600" />
          )}
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all" />
      </div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
        {task.name}
      </h3>

      {task.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="font-mono truncate">{task.id}</span>
        {task.children_ids && task.children_ids.length > 0 && (
          <span className="bg-gray-100 px-2 py-1 rounded">
            {task.children_ids.length} children
          </span>
        )}
      </div>
    </Link>
  );
}
