"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Task {
  id: string;
  name: string;
  category: string;
}

interface Category {
  count: number;
  examples: string[];
}

interface RemovalData {
  categories: Record<string, Category>;
  tasks: Task[];
  total: number;
}

export default function ReviewRemovalPage() {
  const [data, setData] = useState<RemovalData | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    fetch("/data/tasks_to_remove.json")
      .then((r) => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  const toggleCategory = (cat: string) => {
    const newSelected = new Set(selectedCategories);
    if (newSelected.has(cat)) {
      newSelected.delete(cat);
    } else {
      newSelected.add(cat);
    }
    setSelectedCategories(newSelected);
  };

  const selectAll = () => {
    if (data) {
      setSelectedCategories(new Set(Object.keys(data.categories)));
    }
  };

  const getSelectedCount = () => {
    if (!data) return 0;
    const selectedTasks = data.tasks.filter(t => selectedCategories.has(t.category));
    return new Set(selectedTasks.map(t => t.id)).size;
  };

  const getTasksForCategory = (cat: string) => {
    if (!data) return [];
    return data.tasks
      .filter(t => t.category === cat)
      .filter(t => !searchFilter || t.name.toLowerCase().includes(searchFilter.toLowerCase()));
  };

  const handleConfirmRemoval = async () => {
    if (!data) return;

    const tasksToRemove = data.tasks
      .filter(t => selectedCategories.has(t.category))
      .map(t => t.id);

    // Save to localStorage for now
    localStorage.setItem("tasks_to_remove", JSON.stringify(tasksToRemove));
    setConfirmed(true);

    // In production, this would call an API to actually remove them
    alert(`Marked ${tasksToRemove.length} tasks for removal. Export this list to apply changes.`);
  };

  const exportRemovalList = () => {
    if (!data) return;
    const tasksToRemove = data.tasks
      .filter(t => selectedCategories.has(t.category))
      .map(t => ({ id: t.id, name: t.name, category: t.category }));

    const blob = new Blob([JSON.stringify(tasksToRemove, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tasks_to_remove_confirmed.json";
    a.click();
  };

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16 text-center">
        <p>Loading tasks to review...</p>
      </div>
    );
  }

  const categoryDescriptions: Record<string, string> = {
    document_creation: "Tasks that create reports, documents, memos, proposals, articles",
    business_planning: "Business plans, budgets, strategies, policies, objectives",
    analysis_evaluation: "Analyzing, evaluating, assessing, auditing, investigating",
    reading_reviewing: "Reading documents, reviewing applications, interpreting texts",
    communication_presentation: "Presentations, lectures, meetings, discussions, advising",
    management_supervision: "Managing, supervising, coordinating, directing, leading",
    decision_approval: "Approving, authorizing, deciding, recommending, selecting",
    planning_scheduling: "Planning, scheduling, organizing, prioritizing, allocating",
    compliance_legal: "Compliance, regulations, legal requirements, standards",
    financial_accounting: "Financial statements, accounting, invoicing, taxes",
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      {/* Header */}
      <header className="mb-8">
        <Link href="/" className="text-gray-400 hover:text-gray-600 text-sm">
          &larr; Back to home
        </Link>
        <h1 className="text-4xl font-light mt-4 mb-2">Review Non-Physical Tasks</h1>
        <p className="text-gray-500">
          Select categories to remove. These tasks cannot be performed by robots.
        </p>
      </header>

      {/* Stats Bar */}
      <div className="sticky top-0 bg-white border-b border-gray-200 py-4 mb-8 z-10">
        <div className="flex items-center justify-between">
          <div className="flex gap-8">
            <div>
              <span className="text-3xl font-light">{data.total.toLocaleString()}</span>
              <span className="text-gray-400 ml-2">total found</span>
            </div>
            <div>
              <span className="text-3xl font-light text-red-600">
                {getSelectedCount().toLocaleString()}
              </span>
              <span className="text-gray-400 ml-2">selected for removal</span>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={selectAll}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Select All
            </button>
            <button
              onClick={() => setSelectedCategories(new Set())}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear All
            </button>
            <button
              onClick={exportRemovalList}
              disabled={selectedCategories.size === 0}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              Export Removal List
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search within tasks..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="w-full px-4 py-3 border border-gray-200 rounded-lg"
        />
      </div>

      {/* Categories */}
      <div className="space-y-4">
        {Object.entries(data.categories)
          .sort((a, b) => b[1].count - a[1].count)
          .map(([cat, catData]) => {
            const isSelected = selectedCategories.has(cat);
            const isExpanded = expandedCategory === cat;
            const tasks = getTasksForCategory(cat);

            return (
              <div
                key={cat}
                className={`border rounded-lg overflow-hidden ${
                  isSelected ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              >
                {/* Category Header */}
                <div className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleCategory(cat)}
                      className="w-5 h-5 rounded"
                    />
                    <div>
                      <h3 className="font-medium text-lg">
                        {cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {categoryDescriptions[cat] || ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-light">
                      {catData.count.toLocaleString()}
                    </span>
                    <button
                      onClick={() => setExpandedCategory(isExpanded ? null : cat)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"
                    >
                      {isExpanded ? "Hide" : "Show"} Tasks
                    </button>
                  </div>
                </div>

                {/* Examples (always visible) */}
                <div className="px-4 pb-4 border-t border-gray-100">
                  <p className="text-xs text-gray-400 mb-2 mt-2">Examples:</p>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {catData.examples.slice(0, 3).map((ex, i) => (
                      <li key={i} className="truncate">• {ex}</li>
                    ))}
                  </ul>
                </div>

                {/* Expanded Task List */}
                {isExpanded && (
                  <div className="border-t border-gray-200 max-h-96 overflow-y-auto bg-white">
                    <div className="p-4 space-y-2">
                      {tasks.slice(0, 100).map((task) => (
                        <div
                          key={task.id}
                          className="p-3 bg-gray-50 rounded text-sm"
                        >
                          <p className="font-mono text-xs text-gray-400 mb-1">
                            {task.id}
                          </p>
                          <p>{task.name}</p>
                        </div>
                      ))}
                      {tasks.length > 100 && (
                        <p className="text-center text-gray-400 py-4">
                          ... and {tasks.length - 100} more tasks
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
      </div>

      {/* Confirm Section */}
      {selectedCategories.size > 0 && (
        <div className="mt-12 p-8 bg-red-50 border border-red-200 rounded-lg">
          <h2 className="text-xl font-medium text-red-800 mb-4">
            Confirm Removal of {getSelectedCount().toLocaleString()} Tasks
          </h2>
          <p className="text-red-600 mb-6">
            These tasks will be removed from the database. This action identifies
            non-physical, cognitive tasks that robots cannot perform.
          </p>
          <div className="flex gap-4">
            <button
              onClick={exportRemovalList}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Export Removal List (JSON)
            </button>
            <button
              onClick={handleConfirmRemoval}
              className="px-6 py-3 bg-red-800 text-white rounded-lg hover:bg-red-900"
            >
              Confirm & Apply Removal
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
