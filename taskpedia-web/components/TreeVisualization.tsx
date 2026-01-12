'use client';

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { hierarchy, tree } from 'd3-hierarchy';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface TreeNode {
  id: string;
  name: string;
  node_type: string;
  children?: TreeNode[];
}

interface TreeVisualizationProps {
  data: TreeNode;
  height?: number;
  width?: number;
}

export function TreeVisualization({ data, height = 600, width = 1200 }: TreeVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [dimensions, setDimensions] = useState({ width, height });

  useEffect(() => {
    if (!svgRef.current || !data) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const margin = { top: 20, right: 120, bottom: 20, left: 120 };
    const innerWidth = dimensions.width - margin.left - margin.right;
    const innerHeight = dimensions.height - margin.top - margin.bottom;

    // Create SVG container
    const svg = d3.select(svgRef.current)
      .attr('width', dimensions.width)
      .attr('height', dimensions.height);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create tree layout
    const treeLayout = tree<TreeNode>()
      .size([innerHeight, innerWidth]);

    // Create hierarchy
    const root = hierarchy(data);
    const treeData = treeLayout(root);

    // Add links
    g.selectAll('.link')
      .data(treeData.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)
      .attr('d', d3.linkHorizontal<any, any>()
        .x(d => d.y)
        .y(d => d.x)
      );

    // Add nodes
    const nodes = g.selectAll('.node')
      .data(treeData.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.y},${d.x})`);

    // Add circles
    nodes.append('circle')
      .attr('r', 6)
      .attr('fill', d => {
        const type = d.data.node_type;
        const colors: Record<string, string> = {
          DOMAIN: '#3b82f6',
          TASK: '#8b5cf6',
          SUBTASK: '#f97316',
          ATOMIC: '#10b981',
        };
        return colors[type] || '#6b7280';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add labels
    nodes.append('text')
      .attr('dy', '.35em')
      .attr('x', d => d.children ? -10 : 10)
      .attr('text-anchor', d => d.children ? 'end' : 'start')
      .text(d => d.data.name)
      .attr('font-size', '12px')
      .attr('fill', '#1e293b')
      .attr('font-weight', '500');

    // Add node type badges
    nodes.append('text')
      .attr('dy', '1.5em')
      .attr('x', d => d.children ? -10 : 10)
      .attr('text-anchor', d => d.children ? 'end' : 'start')
      .text(d => d.data.node_type)
      .attr('font-size', '9px')
      .attr('fill', '#64748b')
      .attr('font-weight', '600');

  }, [data, dimensions, zoom]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));
  const handleFit = () => setZoom(1);

  return (
    <div className="relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex space-x-2">
        <button
          onClick={handleZoomIn}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
          title="Zoom In"
        >
          <ZoomIn className="w-5 h-5 text-gray-700" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
          title="Zoom Out"
        >
          <ZoomOut className="w-5 h-5 text-gray-700" />
        </button>
        <button
          onClick={handleFit}
          className="p-2 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200"
          title="Fit to Screen"
        >
          <Maximize2 className="w-5 h-5 text-gray-700" />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-md p-3 border border-gray-200">
        <div className="text-xs font-semibold text-gray-700 mb-2">Node Types</div>
        <div className="space-y-1">
          {[
            { type: 'DOMAIN', color: '#3b82f6', label: 'Domain' },
            { type: 'TASK', color: '#8b5cf6', label: 'Task' },
            { type: 'SUBTASK', color: '#f97316', label: 'Subtask' },
            { type: 'ATOMIC', color: '#10b981', label: 'Atomic' },
          ].map(item => (
            <div key={item.type} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-gray-600">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="overflow-auto" style={{ height: dimensions.height }}>
        <svg
          ref={svgRef}
          className="w-full h-full"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
        />
      </div>
    </div>
  );
}
