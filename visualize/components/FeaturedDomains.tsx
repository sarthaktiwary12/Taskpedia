'use client';

import Link from 'next/link';
import {
  Stethoscope,
  Wrench,
  HardHat,
  Home,
  Utensils,
  ShoppingCart,
  GraduationCap,
  Truck
} from 'lucide-react';

const featuredDomains = [
  {
    id: 'work_healthcare',
    name: 'Healthcare',
    description: 'Medical procedures, patient care, and clinical tasks',
    icon: Stethoscope,
    color: 'from-red-500 to-pink-500',
    taskCount: '120K+',
  },
  {
    id: 'work_manufacturing',
    name: 'Manufacturing',
    description: 'Assembly, quality control, and production workflows',
    icon: Wrench,
    color: 'from-blue-500 to-cyan-500',
    taskCount: '95K+',
  },
  {
    id: 'work_construction',
    name: 'Construction',
    description: 'Building, installation, and maintenance tasks',
    icon: HardHat,
    color: 'from-orange-500 to-amber-500',
    taskCount: '88K+',
  },
  {
    id: 'life_household',
    name: 'Household',
    description: 'Cleaning, organizing, and home maintenance',
    icon: Home,
    color: 'from-green-500 to-emerald-500',
    taskCount: '150K+',
  },
  {
    id: 'life_food_prep',
    name: 'Food Preparation',
    description: 'Cooking, meal prep, and kitchen tasks',
    icon: Utensils,
    color: 'from-purple-500 to-violet-500',
    taskCount: '85K+',
  },
  {
    id: 'work_retail',
    name: 'Retail',
    description: 'Inventory, merchandising, and customer service',
    icon: ShoppingCart,
    color: 'from-pink-500 to-rose-500',
    taskCount: '72K+',
  },
  {
    id: 'work_education',
    name: 'Education',
    description: 'Teaching, lab work, and educational activities',
    icon: GraduationCap,
    color: 'from-indigo-500 to-blue-500',
    taskCount: '68K+',
  },
  {
    id: 'work_logistics',
    name: 'Logistics',
    description: 'Warehousing, transport, and supply chain tasks',
    icon: Truck,
    color: 'from-teal-500 to-cyan-500',
    taskCount: '92K+',
  },
];

export function FeaturedDomains() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {featuredDomains.map((domain) => {
        const Icon = domain.icon;
        return (
          <Link
            key={domain.id}
            href={`/domain/${domain.id}`}
            className="group bg-white rounded-2xl p-6 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 hover:scale-105"
          >
            <div className="flex flex-col h-full">
              <div className={`w-14 h-14 bg-gradient-to-br ${domain.color} rounded-xl flex items-center justify-center mb-4 shadow-lg group-hover:shadow-xl transition-shadow`}>
                <Icon className="w-7 h-7 text-white" />
              </div>

              <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                {domain.name}
              </h3>

              <p className="text-sm text-gray-600 mb-4 flex-grow">
                {domain.description}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-500">
                  {domain.taskCount} tasks
                </span>
                <span className="text-primary-600 group-hover:translate-x-1 transition-transform">
                  →
                </span>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
